import configparser
from image_queue import ImageCoords
import main_window
import os
from digitisation import data_io

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('resources/config')
    pdf_dir = config['DEFAULT']['PdfDir']
    img_dir = config['OUTPUTS']['ImgsDir']
    alignment_template = config['RESOURCES']['AlignmentTemplate']
    pixel_template = config['RESOURCES']['PixelTemplate']
    cropped_template = config['RESOURCES']['CroppedTemplate']
    log_file = config['GUI']['LogFile']
    resume_index_file = config['GUI']['ResumeIndexFile']
    source_filenames = config['GUI']['SourceFilenames']
    data_dir = config['DATA']['DataDir']
    resume_index_file = os.path.join(data_dir, resume_index_file)
    source_filenames = os.path.join(data_dir, source_filenames)
    log_file = os.path.join(data_dir, log_file)
    data_io.try_make_dir(data_dir)
    manikin_left_upper_x, manikin_left_upper_y = config['MANIKINAREA']['LeftUpper'].split(',')
    manikin_right_lower_x, manikin_right_lower_y = config['MANIKINAREA']['RightLower'].split(',')
    display_left_upper_x, display_left_upper_y = config['DISPLAYAREA']['LeftUpper'].split(',')
    display_right_lower_x, display_right_lower_y = config['DISPLAYAREA']['RightLower'].split(',')
    manikin_coords = ImageCoords((int(manikin_left_upper_x), int(manikin_left_upper_y)),
                                 (int(manikin_right_lower_x), int(manikin_right_lower_y)))
    display_coords = ImageCoords((int(display_left_upper_x), int(display_left_upper_y)),
                                 (int(display_right_lower_x), int(display_right_lower_y)))
    window = main_window.MainWindow(pdf_dir, img_dir, alignment_template, cropped_template, pixel_template, log_file,
                                    resume_index_file, manikin_coords, display_coords, source_filenames)