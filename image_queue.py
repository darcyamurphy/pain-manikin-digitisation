from digitisation import data_io
import cv2
from PIL import Image
import os
import threading
import pytesseract

def get_all_image_text(image_path: str) -> str:
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    extracted_text = pytesseract.image_to_string(image_rgb)
    return extracted_text

def get_image_text_from_image(image) -> str:
    extracted_text = pytesseract.image_to_string(image)
    return extracted_text

def get_pain_or_stiffness(text: str) -> str:
    pain_count = text.count('pain')
    stiffness_count = text.count('stiffness')
    if pain_count > stiffness_count:
        return 'pain'
    return 'stiffness'


class ImageCoords:
    def __init__(self, left_upper: tuple[int, int], right_lower: tuple[int, int]):
        self.left_upper = left_upper
        self.right_lower = right_lower

class ImageQueue:
    def __init__(self, source_files: list[str], output_dir: str, temp_dir: str, template_file: str, resume_index_file: str,
                 filenames_log_file: str, manikin_coords: ImageCoords, display_coords: ImageCoords, resume: bool = False):
        self.source_files = source_files
        self.output_dir = output_dir
        self.temp_dir = temp_dir

        self.resume_index_file = resume_index_file
        self.filenames_log_file = filenames_log_file

        if not resume:
            self.i = -1
        else:
            self.i = data_io.load_resume_index(resume_index_file)

        template_path = data_io.file_to_png(template_file, self.temp_dir)

        self.template = cv2.imread(template_path)

        manikin_template_img = data_io.load_image_section(template_path,
                                                          manikin_coords.left_upper,
                                                          manikin_coords.right_lower)
        new_filename = os.path.join(self.output_dir, 'template_image.png')
        manikin_template_img.save(new_filename)

        self.full_image = None
        self.cropped_manikin_image = None
        self.manikin_coords = manikin_coords
        self.display_image = None
        self.display_coords = display_coords
        self._lock = threading.Lock()

    def get_next_img(self):
        with self._lock:
            data_io.save_resume_index(self.resume_index_file, self.i)
            self.i += 1
            tmp_aligned_path = None
            while tmp_aligned_path is None and self.i < len(self.source_files):
                f = self.source_files[self.i]
                tmp_aligned_path = data_io.create_temp_aligned_image(f, self.temp_dir, self.template)

            if tmp_aligned_path is None:
                # reached end of files
                data_io.remove_directory(self.temp_dir)
                self.full_image = None
                self.cropped_manikin_image = None
                self.display_image = None
            else:
                self.full_image = Image.open(tmp_aligned_path)
                # clip manikin area and ID
                self.cropped_manikin_image = data_io.load_image_section(tmp_aligned_path,
                                                                        self.manikin_coords.left_upper,
                                                                        self.manikin_coords.right_lower)
                self.display_image = data_io.load_image_section(tmp_aligned_path,
                                                                self.display_coords.left_upper,
                                                                self.display_coords.right_lower)

        return self.full_image, self.cropped_manikin_image, self.display_image

    def save_current_img(self, filename):
        with self._lock:
            cropped_image = self.cropped_manikin_image
            full_image = self.full_image
            i = self.i

        if cropped_image is not None:
            text = get_image_text_from_image(full_image)
            pain_or_stiffness = get_pain_or_stiffness(text)
            # save previous clipped manikin with ID and pain/stiffness as file name in output dir
            new_filename = os.path.join(self.output_dir, f'{pain_or_stiffness}_{filename}.png')
            cropped_image.save(new_filename)
            # add new file name to list with source filename
            data_io.append_filenames_log(self.source_files[i], new_filename, self.filenames_log_file)

    def log_skipped_img(self):
        with self._lock:
            i = self.i
        data_io.append_filenames_log(self.source_files[i], 'skipped', self.filenames_log_file)
