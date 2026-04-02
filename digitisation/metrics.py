import os
from . import data_io
import pandas as pd
import math
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats as st
import cv2
import numpy as np
import imutils

def get_full_df(files: list[str]) -> pd.DataFrame:
    dfs = []
    for f in files:
        dfs.append(pd.read_csv(f))

    full_df = pd.concat(dfs)
    return full_df

def get_alignment_stats(files: list[str], filename_match : str | None = None):
    """

    :param files: List of filenames of alignment log files
    :param filename_match: Optional search string, will only include rows from log where filename column contains
    filename_match
    :return:
    """
    full_df = get_full_df(files)
    original_count = len(full_df)
    if filename_match is not None:
        filename_filter = full_df['filename'].str.contains(filename_match)
        full_df = full_df[filename_filter]
    std_dev = full_df['alignment'].std()
    mean = full_df['alignment'].mean()
    print(f'mean alignment score: {round(mean, 4)}. standard deviation of alignment score: {round(std_dev, 4)}\n'
          f'n={len(full_df)} (excluded {len(full_df)-original_count})')

def jaccard_index(a: set[tuple[int, int]], b: set[tuple[int, int]]) -> float:
    # size of intersection / size of union
    return len(a&b)/len(a|b)

def build_coord_set(coords: list[tuple[int, int]], downscale) -> set[tuple[int, int]]:
    coord_set = set()
    for x,y in coords:
        downscale_x = int(x/downscale)
        downscale_y = int(y/downscale)
        coord_set.add((downscale_x, downscale_y))
    return coord_set

def get_file_list_coords(files: list[str], downscale: int=10):
    all_examples = {}
    for f in files:
        pixels, size = data_io.get_pixels(f)
        coords = data_io.get_coords(pixels, [(255, 0, 0), (255, 0, 0, 255)], size[1])
        coord_set = build_coord_set(coords, downscale)
        filename = os.path.basename(f)
        all_examples[filename] = coord_set
        print(f'file {filename}, {len(coord_set)} coords')
    return all_examples

def calculate_jaccard_indexes(files_a: list[str], files_b: list[str], datafile: str, downscale: int = 10):
    """
    Calculate jaccard index between matched pairs of files. The two file lists should have files with the same names.
    :param files_a:
    :param files_b:
    :param datafile:
    :param downscale:
    :return:
    """
    examples_a = get_file_list_coords(files_a, downscale)
    examples_b = get_file_list_coords(files_b, downscale)

    if not len(examples_a) == len(examples_b):
        print("File lists mismatched length")
        return None

    with open(datafile, 'w') as f:
        f.write('filename,jaccard\n')
        pairwise_distances = {}
        for d in examples_a.keys():
            if len(examples_a[d]) == 0:
                print(f'File {d} contains empty manikin.')
                continue
            if d not in examples_b:
                print(f'File {d} missing from second list.')
                continue

            pairwise_distances[d] = jaccard_index(examples_a[d], examples_b[d])
            f.write(f'{d},{pairwise_distances[d]}\n')
    return None

def analyse_jaccard_indexes(datafile: str):
    pairwise_distances = pd.read_csv(datafile)

    std_dev = pairwise_distances['jaccard'].std()
    mean = pairwise_distances['jaccard'].mean()
    print(f'mean jaccard: {round(mean, 4)}. standard deviation of jaccard: {round(std_dev, 4)}')

def get_pain_extents(files: list[str], template_file: str, datafile: str):
    # pain extent is % of available area so need digitised area and template
    # then just divide num pixels marked by total available pixels
    template_pixels, template_size = data_io.get_pixels(template_file)
    template_coords = data_io.get_coords(template_pixels, [(255, 0, 0), (255, 0, 0, 255)], template_size[1])
    available_pixels = len(template_coords)

    with open(datafile, 'w') as df:
        df.write('filename,pixels,percent\n')
        all_areas = {}
        for f in files:
            pixels, size = data_io.get_pixels(f)
            coords = data_io.get_coords(pixels, [(255, 0, 0), (255, 0, 0, 255)], size[1])
            filename = os.path.basename(f)
            marked_pixels = len(coords)
            all_areas[filename] = marked_pixels
            percent = (marked_pixels / available_pixels) * 100
            print(f'file {filename}, total pixels: {marked_pixels} ({percent:.2f}%)')
            df.write(f'{filename},{marked_pixels},{percent:.2f}\n')

def compare_pain_extents(datafile_a: str, datafile_b: str):
    pain_extents_a = data_io.load_pain_extents(datafile_a)[['filename', 'pixels']]
    pain_extents_b = data_io.load_pain_extents(datafile_b)[['filename', 'pixels']]
    result = pd.merge(pain_extents_a, pain_extents_b, on='filename', suffixes=('_a', '_b')).rename(columns={'pixels_a':'a', 'pixels_b': 'b'})
    bland_altman_plot(result)

def is_pixel_good_surface(gt_img, x: int, y: int, tau: int, match_colour: int) -> int:
    """
    Check if provided pixel coords are within tau pixels of a pixel of match_colour in gt_img.
    Checks in a 2tau by 2tau square around the pixel at (x,y), ignoring pixels outside the boundary of the image.
    :param gt_img:
    :param x: x coord of pixel to check
    :param y: y coord of pixel to chek
    :param tau: allowable distance
    :param match_colour: value of pixels which are part of the surface
    :return: match_colour if there is a matching pixel within range, otherwise 0
    """
    height, width = gt_img.shape
    x_lower = max(x-tau, 0)
    x_upper = min(x+tau, width-1)
    y_lower = max(y-tau, 0)
    y_upper = min(y + tau, height-1)
    for i in range(x_lower, x_upper+1):
        for j in range(y_lower, y_upper+1):
            # coordinates are y,x not x,y!
            if gt_img[j][i] == match_colour:
                return match_colour
    return 0

def get_matching_pixel_count(img, match_colour: int) -> int:
    """
    Get the number of pixels/cells in img that have the value match_colour. Assumes one colour channel.
    :param img:
    :param match_colour:
    :return:
    """
    values, counts = np.unique(img, return_counts=True)
    result = dict(zip(values, counts))
    try:
        count = result[match_colour]
    except KeyError:
        count = 0
    return count

def calculate_dice_surface_distances(files: dict, datafile: str, tau: int, verbose: bool = True):
    """
    Calculate dice surface distance between matched pairs of files. Writes results to csv file in location specified
    by datafile.
    :param files: Dictionary with keys as file paths to ground truth pixel maps and values as file paths to predicted
    pixel maps.
    :param datafile: The output file to save results to.
    :param tau: maximum acceptable distance in pixels between true surface and predicted surface
    :param verbose: Output progress to command line
    :return:
    """
    match_colour = 255
    with open(datafile, 'w') as f:
        f.write('filename,dsc\n')
        for k, v in files.items():
            filename = os.path.basename(k)
            if verbose:
                print(f'processing: {filename}')
            # load ground truth
            gt_img = cv2.imread(k)
            gt_img = cv2.cvtColor(gt_img, cv2.COLOR_BGR2GRAY)
            # load prediction
            p_img = cv2.imread(v)
            p_img = cv2.cvtColor(p_img, cv2.COLOR_BGR2GRAY)
            # nb canny thresholds not super important because the pixel maps should be only two colours with no noise
            # edge detection on ground truth
            gt_edges = cv2.Canny(gt_img, 100, 200)
            matches = np.zeros_like(gt_edges)
            # edge detection on prediction
            p_edges = cv2.Canny(p_img, 100, 200)
            height, width = matches.shape
            for i_x in range(width):
                for j_y in range(height):
                    # coordinates are y,x not x,y!
                    if p_edges[j_y][i_x] == match_colour:
                        matches[j_y][i_x] = is_pixel_good_surface(gt_edges, i_x, j_y, tau, match_colour)

            good_pixels = get_matching_pixel_count(matches, match_colour)
            true_edge_size = get_matching_pixel_count(gt_edges, match_colour)
            predicted_edge_size = get_matching_pixel_count(p_edges, match_colour)
            if true_edge_size + predicted_edge_size == 0:
                # if there are no true edges and we also didn't predict any edges, we were correct
                # but we can't divide by 0 so we just set dsc to 1 to satisfy the laws of mathematics
                dsc = 1
            else:
                dsc = (2*good_pixels) / (true_edge_size + predicted_edge_size)
            if verbose:
                print(f'dsc: {dsc}')
            # todo save debug image

            f.write(f'{filename},{dsc}\n')

def bland_altman_plot(df: pd.DataFrame):
    """
    Takes a dataframe with columns a and b, where each column is an independent measurement of the same value.
    :param df:
    :return:
    """

    df['diff'] = abs(df['a'] - df['b'])
    df['avg'] = (df['a'] + df['b'])/2
    mean_diff = df['diff'].mean()
    standard_deviation = df['diff'].std()
    # use a z value of 1.960 for a confidence interval of 95%
    z = 1.960
    n = len(df)

    ci_lower = mean_diff - z * (standard_deviation / math.sqrt(n))
    ci_upper = mean_diff + z * (standard_deviation / math.sqrt(n))

    agreement = 0.95
    loas = st.norm.interval(agreement, mean_diff, standard_deviation)
    print(f'mean: {round(mean_diff, 4)}, std: {round(standard_deviation, 4)}, 95% CI: ({round(ci_lower, 4)}-{round(ci_upper, 4)})')
    print(f'Limits of agreement (95%): {round(loas[0], 4)}, {round(loas[1], 4)}')
    print(df)
    ax = sns.scatterplot(df, x='avg', y='diff')
    plt.axhline(y=mean_diff, color='r', linestyle='-')
    plt.axhline(y=ci_lower, color='b', linestyle='--')
    plt.axhline(y=ci_upper, color='b', linestyle='--')
    plt.show()
