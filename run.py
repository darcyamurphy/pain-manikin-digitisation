import configparser
import argparse
import os.path
from digitisation import main, data_io
from pathlib import Path
import time

def get_coords(config: configparser.ConfigParser) -> tuple[tuple[int, int], tuple[int, int]]:
    left_upper_x, left_upper_y = config['MANIKINAREA']['LeftUpper'].split(',')
    right_lower_x, right_lower_y = config['MANIKINAREA']['RightLower'].split(',')
    left_upper = (int(left_upper_x), int(left_upper_y))
    right_lower = (int(right_lower_x), int(right_lower_y))
    return left_upper, right_lower

def get_absolute_path(config_section: str, default_dir: str, f_path: str, config: configparser.ConfigParser) -> str:
    """
    Checks if the path to f_path is relative or absolute
    Returns the f_path path if it is absolute, or combines with the default dir path
    if the f_path path is relative
    :param config_section:
    :param default_dir:
    :param f_path: path to file or folder
    :param config:
    :return:
    """
    # todo rename params to make this clearer
    named_dir = config[config_section][f_path]
    if os.path.isabs(named_dir):
        return named_dir
    return os.path.join(config[config_section][default_dir], named_dir)

def check_inputs(dir_name: str, is_input: bool, config: configparser.ConfigParser) -> str | None:
    if is_input and dir_name in config['INPUTS']:
        return config['INPUTS'][dir_name]
    return get_absolute_path('OUTPUTS', 'OutputDir', dir_name, config)

def get_masked_dir(config: configparser.ConfigParser, is_input: bool = False) -> str:
    return check_inputs('MaskedDir', is_input, config)

def get_img_dir(config: configparser.ConfigParser, is_input: bool = False) -> str:
    return check_inputs('ImgsDir', is_input, config)

def get_realigned_dir(config: configparser.ConfigParser, is_input: bool = False) -> str:
    return check_inputs('RealignedDir', is_input, config)

def get_temp_dir(config: configparser.ConfigParser) -> str:
    return get_absolute_path('OUTPUTS', 'OutputDir', 'TempDir', config)

def get_data_dir(config: configparser.ConfigParser) -> str:
    return config['DATA']['DataDir']

def get_alignment_log(config: configparser.ConfigParser) -> str:
    return config['DATA']['AlignmentLog']

def get_debug_dir(config: configparser.ConfigParser) -> str:
    return get_absolute_path('OUTPUTS', 'OutputDir', 'DebugDir', config)

def get_visualisations_dir(config: configparser.ConfigParser) -> str:
    return get_absolute_path('OUTPUTS', 'OutputDir', 'VisualisationsDir', config)

def get_pain_regions_dir(config: configparser.ConfigParser, is_input: bool = False) -> str:
    return check_inputs('PainRegionsDir', is_input, config)

def get_alignment_template(config: configparser.ConfigParser) -> str:
    return config['RESOURCES']['AlignmentTemplate']

def get_raw_dir(config: configparser.ConfigParser) -> str:
    return config['DEFAULT']['RawDir']

def get_pixel_template(config: configparser.ConfigParser) -> str:
    return config['RESOURCES']['PixelTemplate']

def get_filename_map(config: configparser.ConfigParser) -> str:
    return get_absolute_path('DATA', 'DataDir', 'FilenameMap', config)

def get_sections_dir(config: configparser.ConfigParser) -> str:
    return config['RESOURCES']['SectionsDir']

def get_sections_log(config: configparser.ConfigParser) -> str:
    return get_absolute_path('DATA', 'DataDir', 'SectionsLog', config)

def get_min_pixels_per_section(config: configparser.ConfigParser) -> int:
    return int(config['ADVANCED']['MinPixelsPerSection'])

def get_jaccard_dirs(config: configparser.ConfigParser) -> tuple[str, str]:
    return config['JACCARD']['DirA'], config['JACCARD']['DirB']

def get_jaccard_log(config: configparser.ConfigParser) -> str:
    return config['JACCARD']['LogFile']

def get_extent_dir(config: configparser.ConfigParser) -> str:
    return config['EXTENT']['Dir']

def get_extent_template(config: configparser.ConfigParser) -> str:
    return config['EXTENT']['Template']

def get_extent_logfile(config: configparser.ConfigParser) -> str:
    return config['EXTENT']['LogFile']

def get_extent_compare_files(config: configparser.ConfigParser) -> tuple[str, str]:
    return config['EXTENT']['CompareA'], config['EXTENT']['CompareB']

def get_background_colours(config: configparser.ConfigParser) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    l_h, l_s, l_v = config['ADVANCED']['BackgroundColourLowerBound'].split(',')
    u_h, u_s, u_v = config['ADVANCED']['BackgroundColourUpperBound'].split(',')
    lower = int(l_h), int(l_s), int(l_v)
    upper = int(u_h), int(u_s), int(u_v)
    return lower, upper

def get_erosion_value(config: configparser.ConfigParser) -> int:
    return int(config['ADVANCED']['ErosionSize'])

def get_canny_thresholds(config: configparser.ConfigParser) -> tuple[int, int]:
    return int(config['ADVANCED']['LowCannyThreshold']), int(config['ADVANCED']['HighCannyThreshold'])

def get_clustering_thresholds(config: configparser.ConfigParser) -> int:
    return int(config['ADVANCED']['ClusteringThreshold'])

def get_cropped_template(config: configparser.ConfigParser) -> str:
    """
    The location to be used for the cropped image from the pdf template. Will be automatically generated when aligning
    images.
    :param config:
    :return:
    """
    return config['RESOURCES']['CroppedTemplate']

def get_files_from_dir_or_list(file_list: str or None, source_dir: str, prepend_path: str, extension: str) -> list[str]:
    # todo be more consistent about if file list needs to have full path to file or not
    if file_list is not None:
        files = data_io.load_source_files_list(file_list)
        files = [os.path.join(prepend_path, f) for f in files]
    else:
        files = data_io.get_source_files(source_dir, extension)

    return files

def get_extension(args_extension: str | None, default_extension: str) -> str:
    if args_extension is None:
        return default_extension
    return args_extension

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--align', action='store_true',
                        help='Align files in PdfDir to match AlignmentTemplate and crop to MANIKINAREA coords. Output '
                             'saved in ImgDir')
    parser.add_argument('--pixel_mask', action='store_true',
                        help='Apply pixel mask from PixelTemplate to files in ImgDir and save to MaskedDir.'
                             ' Not necessary to run this before preprocessing, this is done automatically as part of'
                             'preprocessing.')
    parser.add_argument('-r', '--rename', action='store_true',
                        help='Use filenames from FilenameMap to rename source files while aligning.')
    parser.add_argument('-e', '--realign', default=None,
                        help='Realign specified image to template. Assumes image is mostly just manikin area.')
    parser.add_argument('-s', '--sections', action='store_true',
                        help='Compare images in ImgDir to sections in SectionsDir')
    parser.add_argument('-u', '--hull', action='store_true',
                        help='Show convex hull for images in CleanedDir')
    parser.add_argument('-j', '--jaccard', action='store_true',
                        help='Calculate jaccard index between files in directory JaccardA and JaccardB. All files in'
                             'directory A must have a file with matching name in directory B.')
    parser.add_argument('--jaccard_metrics', action='store_true',
                        help='Output stats on jaccard metrics in Jaccard LogFile')
    parser.add_argument('-x', '--extent', action='store_true',
                        help='Calculate pain extents of files in Extent')
    parser.add_argument('--cextent', action='store_true',
                        help='Compare pain extents of CompareA and CompareB in Extent')
    parser.add_argument('--preprodemo', action='store_true',
                        help='Demonstrate preprocessing for troubleshooting purposes. White lines will be blanked out.')
    parser.add_argument('-p', '--preprocessing', action='store_true',
                        help='Preprocess files in IngsDir and save to CleanedDir.')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('-v', '--visualise', action='store_true',
                        help='Save visualisations of convex hulls.')
    parser.add_argument('--heatmap',
                        help='Create heatmap of files in PainRegionsDir and save to provided filename')
    parser.add_argument('--file_list',
                        help='Specify a file with a list of source files to override searching default input dir')
    parser.add_argument('--heatmap_num_override',
                        help='Override the actual number of images when weighting images for heatmap. Can be used'
                             'to harmonise heatmaps when one has less images than the other.')
    parser.add_argument('--extension',
                        help= 'Override default extension for directory search')
    parser.add_argument('--config', help='Specify non-default config file', default='resources/config')
    parser.add_argument('--resume_index', type=int, default=-1,
                        help='Specify a number to resume from when calculating marked sections from a file list. Don\'t '
                             'use when getting file from a directory rather than a list as they may not be in the same'
                             ' order.')
    parser.add_argument('--alpha', help='Apply contrast filter when preprocessing using this alpha')
    parser.add_argument('--beta', help='Apply brightness filter when preprocessing using this beta')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    if args.align:
        pdf_dir = get_raw_dir(config)
        img_dir = get_img_dir(config)
        temp_dir = get_temp_dir(config)
        data_dir = get_data_dir(config)
        alignment_template = get_alignment_template(config)
        alignment_log = get_alignment_log(config)
        cropped_template = get_cropped_template(config)

        left_upper, right_lower = get_coords(config)
        hsv_lower, hsv_upper = get_background_colours(config)

        if args.rename:
            map_file = get_filename_map(config)
            filenames_map = data_io.load_filenames_log(map_file)
        else:
            # just means we don't need to think about doing anything differently whether or not we're renaming files
            # from this point forward
            extension = get_extension(args.extension, '.pdf')
            filenames = get_files_from_dir_or_list(args.file_list, pdf_dir, '', extension)
            filenames_map = {}
            for f in filenames:
                filenames_map[f] = f'{Path(f).stem}.png'
        # todo use filename from cropped template for the template image that is generated
        main.standard_alignment(img_dir, temp_dir, data_dir,
                                filenames_map, alignment_template, cropped_template,
                                os.path.join(data_dir, alignment_log),
                                left_upper, right_lower, hsv_lower, hsv_upper)

    if args.pixel_mask:
        print('Applying pixel mask')
        pixel_template = get_pixel_template(config)
        img_dir = get_img_dir(config, True)
        masked_dir = get_masked_dir(config)
        main.pixel_mask(img_dir, masked_dir, pixel_template)

    if args.realign is not None:
        print('Realigning')
        output_dir = get_realigned_dir(config)
        temp_dir = get_temp_dir(config)
        alignment_template = get_alignment_template(config)
        left_upper, right_lower = get_coords(config)
        main.realign_image(output_dir, temp_dir, alignment_template, left_upper, right_lower, args.realign)

    if args.preprodemo:
        print('Preprocessing demo')
        lower, upper = get_background_colours(config)
        erosion = get_erosion_value(config)
        template_img = get_cropped_template(config)
        main.preprocessing_demo(template_img, lower, upper, erosion)

    if args.preprocessing:
        print('Preprocessing')
        lower, upper = get_background_colours(config)
        erosion = get_erosion_value(config)
        template_img = get_cropped_template(config)
        img_dir = get_img_dir(config, True)
        output_dir = get_masked_dir(config)
        alpha = 1.0
        beta = 0
        if args.alpha is not None:
            try:
                alpha = float(args.alpha)
            except ValueError:
                print(f'{args.alpha} is not a valid alpha value. Must be a float.')
        if args.beta is not None:
            try:
                beta = int(args.beta)
            except ValueError:
                print(f'{args.beta} is not a valid beta value. Must be an int')

        main.preprocess_dir(img_dir, output_dir, template_img, lower, upper, erosion, alpha, beta)

    if args.sections:
        print('Finding sections')
        masked_dir = get_masked_dir(config, True)
        sections_dir = get_sections_dir(config)
        output_file = get_sections_log(config)
        min_pixels = get_min_pixels_per_section(config)
        low, high = get_canny_thresholds(config)
        extension = get_extension(args.extension, '.png')
        images = get_files_from_dir_or_list(args.file_list, masked_dir, masked_dir, extension)
        print(f'Finding sections for {len(images)} images')
        main.find_marked_regions_in_images(images, sections_dir, output_file, min_pixels, low, high, args.debug,
                                           args.resume_index)

    if args.hull:
        print('Finding hulls')
        img_dir = get_img_dir(config, True)
        masked_dir = get_masked_dir(config, True)
        output_dir = get_pain_regions_dir(config)
        debug_dir = get_debug_dir(config)
        vis_dir = get_visualisations_dir(config)
        extension = get_extension(args.extension, '.png')
        masked_images = get_files_from_dir_or_list(args.file_list, masked_dir, masked_dir, extension)
        low, high = get_canny_thresholds(config)
        clustering_threshold = get_clustering_thresholds(config)
        pixel_mask = get_pixel_template(config)
        print(f'Processing {len(masked_images)} images')
        start = time.time()
        for i in masked_images:
            if args.visualise:
                source_img = data_io.get_matched_file(i, img_dir)
            else:
                source_img = ''
            main.get_convex_hulls(i, low, high, output_dir, clustering_threshold, source_img,
                                  'hierarchical', args.debug, debug_dir,
                                  args.visualise, vis_dir, pixel_mask)
        end = time.time()
        print(f'Time: {end-start}s')

    if args.jaccard:
        # todo add option to load file list from file rather than getting all files in dir
        jaccard_a, jaccard_b = get_jaccard_dirs(config)
        jaccard_log = get_jaccard_log(config)
        main.run_jaccard(jaccard_a, jaccard_b, jaccard_log)

    if args.jaccard_metrics:
        main.analyse_jaccard(get_jaccard_log(config))

    if args.extent:
        extent_dir = get_extent_dir(config)
        extension = get_extension(args.extension, '.png')
        files = get_files_from_dir_or_list(args.file_list, extent_dir, extent_dir, extension)

        extent_log = get_extent_logfile(config)
        extent_template = get_extent_template(config)
        main.run_pain_extents(files, extent_template, extent_log)

    if args.cextent:
        datafile_a, datafile_b = get_extent_compare_files(config)
        main.compare_pain_extents(datafile_a, datafile_b)

    if args.heatmap is not None:
        if args.heatmap_num_override is not None:
            heatmap_num = int(args.heatmap_num_override)
        else:
            heatmap_num = -1

        input_dir = get_pain_regions_dir(config, True)
        extension = get_extension(args.extension, '.png')
        files = get_files_from_dir_or_list(args.file_list, input_dir, "", extension)

        main.generate_heatmap(files, args.heatmap, heatmap_num)

if __name__ == '__main__':
    run()

