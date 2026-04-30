import pandas as pd
import argparse
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import cv2
import matplotlib
import imutils


def jaccard_vs_alignment(jaccard_file, alignment_file):
    alignment_df = pd.read_csv(alignment_file)
    jaccard_df = pd.read_csv(jaccard_file)
    joined = pd.merge(alignment_df, jaccard_df, on='filename')
    sns.scatterplot(joined, x='alignment', y='jaccard')
    plt.show()

def two_jaccard_vs_alignment(jaccard_file_1, j1_name, jaccard_file_2, j2_name, alignment_file):
    alignment_df = pd.read_csv(alignment_file)
    jaccard_1_df = pd.read_csv(jaccard_file_1)
    jaccard_1_df['label'] = j1_name
    jaccard_2_df = pd.read_csv(jaccard_file_2)
    jaccard_2_df['label'] = j2_name
    joined = pd.merge(alignment_df, jaccard_1_df, on='filename')
    joined_2 = pd.merge(alignment_df, jaccard_2_df, on='filename')
    data = pd.concat([joined, joined_2])
    print(data)
    sns.scatterplot(data, x='alignment', y='jaccard', hue='label')
    plt.show()

def body_region_heatmap(region_file: str):
    """
    Generate a heatmap using pixel maps of predefined body regions paired with values between 0 and 1. An image will
    be generated where the region marked in each of the provided pixel maps is coloured according to the associated
    value.
    :param region_file: A csv file with a path column and a value column. The path column should give file paths to
    pixel maps which all have the same dimensions, with the marked region in each covering a distinct non-overlapping
    region of the total area. The value column should be the weighting to be given to the associated region in the final
     heatmap.
    :return:
    """
    df = pd.read_csv(region_file)
    palette = sns.color_palette("crest", as_cmap=True)
    # make blank image of correct dimensions
    example_file = df['path'].iloc[0]
    example_img = cv2.imread(example_file)
    bg_colour = (255, 255, 255)
    heatmap_img = np.zeros(example_img.shape, np.uint8)
    heatmap_img[:] = bg_colour

    # for each pixel map, colour the marked region in the colour indicated by the palette
    for i in range(len(df)):
        row = df.iloc[i]
        pixel_map = cv2.imread(row['path'])
        value = float(row['value'])
        # convert rgb % values from the seaborn colour map into bgr absolute values for opencv
        c = palette(value)
        colour = [c[2]*255, c[1]*255, c[0]*255]

        # threshold image to get area that isn't background colours
        region_mask = cv2.inRange(pixel_map, bg_colour, bg_colour)

        # invert mask to get background area
        bg_mask = cv2.bitwise_not(region_mask)

        # mask out specified region in composite heatmap image
        heatmap_img = cv2.bitwise_or(heatmap_img, heatmap_img, mask=region_mask)

        # create image of correct colour and mask out all pixels not part of specified region
        region_colour_img = np.zeros(example_img.shape, np.uint8)
        region_colour_img[:] = colour
        region_colour_img = cv2.bitwise_or(region_colour_img, region_colour_img, mask=bg_mask)

        # add specified region to composite heatmap image
        heatmap_img = cv2.bitwise_or(heatmap_img, region_colour_img)

    show_img = imutils.resize(heatmap_img, 1000)
    cv2.imshow('composite heatmap', show_img)
    cv2.waitKey(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--jaccard', help='csv file with jaccard index scores')
    parser.add_argument('-a', '--alignment', help='csv file with alignment scores')
    parser.add_argument('--jaccard2', help='optional csv file with second set of jaccard indices')
    parser.add_argument('--j1_label', help='label for points from first jaccard index file when plotting'
                                           'two sets of points', default='set 1')
    parser.add_argument('--j2_label', help='label for second set of jaccard index scores when plotting'
                                           'two sets of points', default='set 2')
    parser.add_argument('--heatmap_file', help='path to csv file with a path column and a value column')
    args = parser.parse_args()

    if args.jaccard2 is None and args.jaccard:
        jaccard_vs_alignment(args.jaccard, args.alignment)
    elif args.jaccard2 and args.jaccard:
        two_jaccard_vs_alignment(args.jaccard, args.j1_label, args.jaccard2, args.j2_label, args.alignment)
    elif args.heatmap_file:
        body_region_heatmap(args.heatmap_file)

