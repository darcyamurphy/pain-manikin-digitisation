import pathlib

import pandas as pd
import pdf2image
from PIL import Image
from pathlib import Path
import os
import shutil
import cv2
from . import image_processing

def get_matched_file(source_file: str, search_dir: str):
    """
    Given a path to a source file, find a file with the same file name in the search dir
    :param source_file:
    :param search_dir:
    :return:
    """
    return pathlib.Path(search_dir).joinpath(pathlib.Path(source_file).name)

def apply_template_mask(image_dir: str, output_dir: str, template_file: str):
    files = get_source_files(image_dir, '.png')
    template_img = Image.open(template_file)
    width, height = template_img.size
    num_channels = 3
    pixel_mask = image_processing.get_pixel_locs(template_img.getdata(), [(255, 0, 0, 255)])
    for f in files:
        f_img = Image.open(f)
        cropped_img = image_processing.crop_to_mask(f_img.getdata(), pixel_mask)
        new_filename = os.path.join(output_dir, Path(f).stem + '.png')
        reshaped_pixels = cropped_img.reshape((height, width, num_channels))
        image = Image.fromarray(reshaped_pixels.astype('uint8'), 'RGB')
        image.save(new_filename)

def load_pdf(filepath: str) -> Image:
    # should only be one page
    image = pdf2image.convert_from_path(filepath, 300)[0]
    return image

def file_to_png(source_file: str, save_dir: str) -> str:
    """
    Takes path to pdf or image file and saves as png in save dir
    :param source_file: The path to the pdf or image input file
    :param save_dir: The directory to save the png in
    :return: The path to the png file
    :return: The path to the png file
    """
    _, extension = os.path.splitext(source_file)
    # if pdf, convert to image file and save in temp image dir
    # otherwise just load the raw image directly
    if 'pdf' in extension or 'PDF' in extension:
        image = load_pdf(source_file)
    else:
        image = Image.open(source_file)

    filename = Path(source_file).stem
    file_out = os.path.join(save_dir, f'{filename}.png')
    image.save(file_out, 'png')
    return file_out

def load_image_section(filepath: str, left_upper: (int, int), right_lower: (int, int)) -> Image:
    """
    Load an image from file and crop to the specified section
    :param filepath:
    :param left_upper:
    :param right_lower:
    :return: The cropped image
    """
    full_image = Image.open(filepath)
    x_upper, y_upper = left_upper
    x_lower, y_lower = right_lower
    cropped = full_image.crop((x_upper, y_upper, x_lower, y_lower))
    return cropped

def remove_directory(dir_path: str):
    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        print(e)

def save_source_files_list(source_files: list[str], output_dir: str, filename: str):
    with open(os.path.join(output_dir, filename), 'w') as f:
        for source_file in source_files:
            f.write(f'{source_file}\n')

def load_source_files_list(file_path: str) -> list[str]:
    files = []
    with open(file_path, 'r') as f:
        for line in f:
            files.append(line.strip())
    return files

def create_alignment_log(log_path: str):
    with open(log_path, 'w') as f:
        f.write('filename,alignment\n')

def append_alignment_log(log_path: str, aligned_filename: str, alignment_rating: float):
    with open(log_path, 'a') as f:
        f.write(f'{aligned_filename},{round(alignment_rating, 4)}\n')

def create_filenames_log(output_dir: str, resume_index_path: str, filenames_list_path: str):
    with open(os.path.join(output_dir, filenames_list_path), 'w') as f:
        f.write('source_file,new_file\n')
    with open(os.path.join(output_dir, resume_index_path), 'w') as f:
        f.write('-1')

def append_filenames_log(source_filename: str, aligned_filename: str, filenames_list_path: str):
    """
    Appends the latest filename pair and updates resume index in resume files
    :param source_filename: The filename of the source pdf for the aligned image
    :param aligned_filename: The filename of the aligned and cropped image
    :param filenames_list_path: The path of the file to append the filename pair to
    :return:
    """
    with open(filenames_list_path, 'a') as f:
        f.write(f'{os.path.basename(source_filename)},{os.path.basename(aligned_filename)}\n')

def load_filenames_log(filenames_list_path: str) -> dict:
    filenames_map = {}
    header_line = True
    with open(filenames_list_path, 'r') as f:
        for l in f:
            if header_line:
                header_line = False
                continue
            source_file, new_file = l.strip().split(',')
            filenames_map[source_file] = new_file
    return filenames_map

def load_resume_index(resume_index_path: str) -> int:
    with open(resume_index_path, 'r') as f:
        index_string = f.readlines()[0].strip()
    return int(index_string)

def save_resume_index(resume_index_path: str, resume_index: int):
    with open(resume_index_path, 'w') as f:
        f.write(f'{resume_index}')

def get_source_files(source_dir: str, extension: str) -> list[str]:
    """
    Check source dir exists and get files from source dir with matching extension
    :param source_dir:
    :param extension:
    :return: paths of all matching files in source dir
    """
    # check source dir exists
    if not os.path.isdir(source_dir):
        raise FileNotFoundError(source_dir)

    files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if Path(f).suffix == extension]
    return files

def create_sub_dir(output_dir: str, subdir: str = 'temp') -> str:
    """
    Create temp output dir
    :param output_dir:
    :param subdir: name to give subdir in output_dir
    :return: path to temp output dir
    """
    # create temp and output dir if doesn't exist
    temp_dir = os.path.join(output_dir, subdir)
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir

def try_make_dir(dir_path: str):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def create_temp_aligned_image(source_file: str, temp_dir: str, template_image) -> str | None:
    """
    Align source pdf to template image and save as png
    :param source_file: The path to the unaligned pdf or image file
    :param temp_dir: The directory to save temp images to
    :param template_image: The cv2 image to align the pdf to
    :return: Path to aligned png or None if image can't be aligned and saved
    """
    # convert to image file and save in temp image dir
    tmp_raw_path = file_to_png(source_file, temp_dir)
    # align image
    full_image = cv2.imread(tmp_raw_path)
    aligned_image = image_processing.align_images(full_image, template_image)
    path_stem = Path(source_file).stem
    tmp_aligned_path = os.path.join(temp_dir, f'{path_stem}-aligned.png')
    success = cv2.imwrite(tmp_aligned_path, aligned_image)
    if not success:
        return None
    return tmp_aligned_path

def align_image(source_image: str, output_path: str, template_image) -> str | None:
    """
    Align source image to template image and save as png
    :param source_image:
    :param output_path:
    :param template_image:
    :return:
    """
    full_image = cv2.imread(source_image)
    aligned_image = image_processing.align_images(full_image, template_image)
    success = cv2.imwrite(output_path, aligned_image)
    if not success:
        return None
    return output_path

def align_directory(source_dir, output_dir, template_file):
    template = cv2.imread(template_file)
    files = get_source_files(source_dir, '.png')
    for f in files:
        path_stem = Path(f).stem
        tmp_aligned_path = os.path.join(output_dir, f'{path_stem}-aligned.png')
        img_path = align_image(f, tmp_aligned_path, template)

def get_pixels(filename):
    image = Image.open(filename)
    pixels = image.getdata()
    return pixels, image.size

def get_pixel_coords(index, width):
    x = index % width
    y = int((index - x) / width)
    return x, y

def get_coords(pixels, inclusion_color: list[tuple[int, int, int]], width) -> list[tuple[int, int]]:
    coords = []
    for i in range(len(pixels)):
        if pixels[i] in inclusion_color:
            coords.append(get_pixel_coords(i, width))
    return coords

def load_pairwise_distances(filename: str) -> dict[str, float]:
    lines = []
    with open(filename, 'r') as f:
        for line in f:
            lines.append(line)

    pairwise_distances = {}
    for line in lines:
        g1,dist = line.strip().split(',')
        if not dist[0].isnumeric():
            # make sure we skip the header row
            continue
        pairwise_distances[g1] = float(dist)
    return pairwise_distances

def load_pain_extents(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename)
    return df

def create_regions_csv(regions: list[str], filename: str) -> bool:
    """
    Try to create file for regions csv file with specified regions as column headers.
    :param regions: The names of the regions
    :param filename: The file path to create.
    :return: True if file created successfully, otherwise false.
    """
    try:
        with open(filename, 'x') as f:
            # make the resulting csv file a bit nicer by putting the columns in alphabetical order
            columns = sorted([Path(s).stem for s in regions])
            filename_header = 'filename'
            f.write(filename_header)
            for c in columns:
                f.write(f',{c}')
    except OSError:
        print(f'Could not create file {filename}, does it already exist?')
        return False
    return True

def append_to_regions_csv(row: list[str], img_filename: str, out_filename: str) -> bool:
    """
    Try to append a row to the regions csv file.
    :param row: A list of the regions which did contain pain. These need to match the header row of out_filename
    :param img_filename: The name of the file the regions were detected in
    :param out_filename: The file to write to
    :return: True if row was appended successfully, otherwise False (e.g. header rows mismatch,file does not exist)
    """
    try:
        with open(out_filename, 'r') as f:
            line = f.readline()
    except OSError:
        print(f'Could not read from {out_filename}.')
        return False

    # first column should be the filename column so we don't include it in the header row list as we know we just
    # write the filename first
    header_row = line.split(',')[1:]
    try:
        with open(out_filename, 'a') as f:
            f.write(f'\n{img_filename}')
            # write True if the column from the file is included in the row list, and False if it isn't
            # write to the file in the same order as the header row that we read from the file
            for h in header_row:
                f.write(f',{h in row}')
    except OSError:
        print(f'Could not write to {out_filename}')
        return False

    return True