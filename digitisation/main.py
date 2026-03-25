from . import data_io, image_processing, metrics
import cv2
import os
from pathlib import Path
import time

def create_template(data_dir: str, temp_dir: str, alignment_template: str, cropped_template_path: str,
                    left_upper: tuple[int, int], right_lower: tuple[int, int]):
    # check directories exist and create them if not
    data_io.try_make_dir(data_dir)
    data_io.try_make_dir(temp_dir)

    # create cropped alignment template
    template_png_path = data_io.file_to_png(alignment_template, temp_dir)
    template_png = cv2.imread(template_png_path)
    image_section = data_io.load_image_section(template_png_path, left_upper, right_lower)
    image_section.save(cropped_template_path)
    cv2_image_section = cv2.imread(cropped_template_path)

    return template_png, cv2_image_section

def standard_alignment(img_dir: str, temp_dir: str, data_dir: str,
                       filenames_map: dict, alignment_template: str, cropped_template_path: str,
                       alignment_log_path: str,
                       left_upper: tuple[int, int], right_lower: tuple[int, int],
                       hsv_lower: tuple[int, int, int], hsv_upper: tuple[int, int, int]):
    """
    Align and crop every image named in filename map which is present in input_dir to the alignment template.
    Also outputs a cropped alignment template consisting of the region specified by the left_upper and right_lower
    coordinates. This should contain just the manikin and not extras like preamble text.
    :param img_dir: The directory to save aligned images to
    :param temp_dir: The temp directory to save interim files to
    :param data_dir: The directory that template files should be saved to
    :param filenames_map: A dictionary where the keys are the filenames in the input dir and the values are the
    filenames that the input files should be saved as. These can be the same if files don't need to be renamed.
    :param alignment_template: Path to a blank pdf of the manikin template used for the input images.
    :param cropped_template_path: The path to save the cropped manikin template to
    :param alignment_log_path: The path to save the log of alignment ratings to
    :param left_upper: The coordinates of the left upper corner of the bounding box that the alignment template should
    be cropped to.
    :param right_lower: The coordinates of the right lower corner of the bounding box that the alignment template should
    be cropped to.
    :param hsv_lower: The lower bound of the background colour
    :param hsv_upper: The upper bound of the background colour
    :return:
    """
    print(f'Converting {len(filenames_map.keys())} files')
    start = time.time()
    # check directories exist and create them if not
    data_io.try_make_dir(data_dir)
    data_io.try_make_dir(temp_dir)
    data_io.try_make_dir(img_dir)

    full_template, cropped_template = create_template(data_dir, temp_dir, alignment_template, cropped_template_path,
                                                      left_upper, right_lower)

    data_io.create_alignment_log(alignment_log_path)

    for f in filenames_map.keys():
        if not os.path.exists(f):
            print(f'{f} not found')
            continue
        else:
            print(f'converting {f}')
        # first alignment pass
        tmp_aligned_path = data_io.create_temp_aligned_image(f, temp_dir, full_template)
        # crop to manikin section
        cropped_manikin_image = data_io.load_image_section(tmp_aligned_path, left_upper, right_lower)
        cropped_manikin_image.save(tmp_aligned_path)
        # second alignment pass
        output_path = os.path.join(img_dir, filenames_map[f])
        print(f'saving {output_path}')
        success = data_io.align_image(tmp_aligned_path, output_path, cropped_template)
        if success is None:
            print(f'error saving {output_path}')
        else:
            alignment_rating = image_processing.get_alignment_rating(cropped_template_path, output_path, hsv_lower, hsv_upper)
            data_io.append_alignment_log(alignment_log_path, filenames_map[f], alignment_rating)
    end = time.time()
    print(f'Time: {end-start}')

def realign_image(output_dir: str, temp_dir: str, alignment_template: str,
                  left_upper: tuple[int, int], right_lower: tuple[int, int],
                  input_img: str):
    full_template, cropped_template = create_template(output_dir, temp_dir, alignment_template, left_upper, right_lower)
    filename = Path(input_img).stem
    output_path = os.path.join(output_dir, f'{filename}-aligned.png')
    success = data_io.align_image(input_img, output_path, cropped_template)
    if success is None:
        print(f'error saving {output_path}')
    else:
        print(f'Saved to {output_path}')

def pixel_mask(img_dir: str, masked_dir: str, pixel_template: str):
    data_io.try_make_dir(masked_dir)
    mask = image_processing.get_mask(pixel_template, (0, 0, 255))
    files = data_io.get_source_files(img_dir, '.png')

    for f in files:
        img = cv2.imread(f)
        masked_image = image_processing.remove_template_pixels(img, (255, 255, 255), mask)
        new_filename = os.path.join(masked_dir, Path(f).stem + '.png')
        success = cv2.imwrite(new_filename, masked_image)

def find_marked_regions_in_images(images: list[str], sections_dir: str, output_file: str, min_pixels: int, low_threshold: int,
                                  high_threshold: int, debug: bool = False, resume_index: int=-1):
    """
    Get the marked body regions for each image in a specified directory and save the results to csv
    :param images: List of files with the cleaned and aligned images, with template outline removed
    :param sections_dir: The directory with images with the pixels for each section marked in red
    :param output_file: The file to save the results to. If file already exists and no resume index is specified,
    will return an error to avoid overwriting existing data. If a resume index is specified the file must already exist.
    :param min_pixels: The minimum number of pixels in a section for that section to be considered marked
    :param low_threshold: The low threshold for canny edge detection when finding drawn lines
    :param high_threshold: The high threshold for canny edge detection when finding drawn lines
    :param debug: Show debug info
    :param resume_index: If non-negative value is specified, will resume processing from the index specified in
    images. E.g. if resume index is 5, the first image processed will be images[5]. If the resume index is specified
    :return:
    """
    sections = data_io.get_source_files(sections_dir, '.png')

    if resume_index < 0:
        success = data_io.create_regions_csv(sections, output_file)
        if not success:
            # if we couldn't create the file then it probably already exists and we shouldn't be appending to it
            return
        resume_index = 0
    start = time.time()
    # start from 0 or specified resume index
    for i in range(resume_index, len(images)):
        img = images[i]
        print(f'Resume index: {i}\nGetting sections for {img}')
        marked_sections = image_processing.get_marked_regions(img, sections, min_pixels, low_threshold, high_threshold,
                                                              debug)
        marked_sections = [Path(f).stem for f in marked_sections]
        if debug:
            print(marked_sections)
        success = data_io.append_to_regions_csv(marked_sections, os.path.basename(img), output_file)
        if not success:
            return
    end = time.time()
    print(f'Time: {end-start}')

def get_convex_hulls(input_img: str, low_threshold: int, high_threshold: int, output_dir: str,
                     clustering_threshold: int,
                     source_image: str='',
                     method: str = 'hierarchical', debug: bool = False, debug_dir: str = '', visualise:bool= True,
                     vis_dir: str = '', pixel_mask_template: str = ''):
    """

    :param input_img:
    :param low_threshold: The lower bound of colours to treat as background colour (BGR)
    :param high_threshold: The upper bound of colours to treat as background colour (BGR)
    :param clustering_threshold: The threshold to use when clustering nearby contours. A higher threshold will give
    bigger clusters.
    :param output_dir: The directory to save pixel maps of found pain regions to.
    :param debug: Whether to output images of found contours. If true, must specify debug_dir.
    :param source_image: If visualise is true and a source image is provided, the convex hulls will be drawn onto the source
    image and saved to the debug folder.
    :param method:
    :param debug_dir: Must be specified if debug = True. The directory to save debug images to.
    :param visualise: Whether to output visualisation of convex hull drawn over original image. If True, must specify
    source_image and vis_dir
    :param vis_dir: The directory to save visualisations to.
    :param pixel_mask_template: The manikin pixel template
    :return:
    """
    image_processing.get_convex_hull(input_img, low_threshold, high_threshold, output_dir, clustering_threshold,
                                     source_image, method, debug, debug_dir, visualise, vis_dir, pixel_mask_template)

def run_jaccard(jaccard_dir_a: str, jaccard_dir_b: str, log_file: str):
    files_a = data_io.get_source_files(jaccard_dir_a, '.png')
    files_b = []
    for f in files_a:
        files_b.append(data_io.get_matched_file(f, jaccard_dir_b))
    metrics.calculate_jaccard_indexes(files_a, files_b, log_file)

def analyse_jaccard(data_file: str):
    metrics.analyse_jaccard_indexes(data_file)

def run_pain_extents(files: list[str], template_file: str, log_file: str):
    metrics.get_pain_extents(files, template_file, log_file)

def compare_pain_extents(datafile_a: str, datafile_b: str):
    metrics.compare_pain_extents(datafile_a, datafile_b)

def preprocessing_demo(template_file: str, background_lower: tuple[int, int, int], background_upper: tuple[int, int, int], erosion_size: int):
    """
    Demonstrate preprocessing steps to check template lines are correctly removed
    :param template_file: Path to pixel template file
    :param background_lower: HSV lower bound for background colour in template
    :param background_upper: HSV upper bound for background colour in template
    :param erosion_size: How much to expand template lines to make sure lines fully overlap manikin outline in aligned images
    :return:
    """
    image_processing.demo_template_pixels(template_file, background_lower, background_upper, erosion_size)

def preprocess_dir(input_dir: str, output_dir: str, template_file: str,
                   background_lower: tuple[int, int, int],
                   background_upper: tuple[int, int, int], erosion_size: int,
                   alpha: float = 1.0, beta: int = 0):
    """
    Preprocess images in a specified directory to remove template lines and isolate marks made by participants.
    :param input_dir: Directory of aligned pain drawings
    :param output_dir: Directory to save preprocessed images to
    :param template_file: Path to pixel template file
    :param background_lower: HSV lower bound for background colour in template
    :param background_upper: HSV upper bound for background colour in template
    :param erosion_size: How much to expand template lines to make sure lines fully overlap manikin outline in aligned images
    :param alpha: Contrast adjustment
    :param beta: brightness adjustment
    :return:
    """
    start = time.time()
    template_mask = image_processing.get_template_mask(template_file, background_lower, background_upper, erosion_size)

    files = data_io.get_source_files(input_dir, '.png')
    data_io.try_make_dir(output_dir)

    print(f'Processing {len(files)} files')
    for f in files:
        filename = os.path.basename(f)
        output_file = os.path.join(output_dir, filename)
        img = cv2.imread(f)

        # remove any remaining pixels from the template lines
        img = image_processing.remove_template_pixels(img, background_upper, template_mask)

        # apply filters to remove some noise
        img = image_processing.apply_preprocessing_filters(img, alpha, beta)

        img = image_processing.remove_light_pixels(img, background_lower, background_upper)

        success = cv2.imwrite(output_file, img)
        print(f'{output_file}, {success}')
    end = time.time()
    print(f'Time: {end-start}')

def generate_heatmap(files: list[str], output_path: str, override_num_images: int=-1):
    avg = image_processing.pixel_average_from_list(files, override_num_images)
    avg.save(output_path)