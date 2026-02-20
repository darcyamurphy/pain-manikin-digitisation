import numpy as np
import imutils
import cv2
import math
from sklearn.cluster import AgglomerativeClustering
import pathlib
import os
import scipy.cluster.hierarchy as hcluster
import scipy.spatial.distance as sdistance
from . import data_io
from PIL import Image

def debug_save(source_image_path: str, output_folder_path: str, debug_img, extra_text: str=''):
    # todo move to data_io
    output_name = pathlib.Path(source_image_path).stem
    if extra_text == '':
        output_path = os.path.join(output_folder_path, f'{output_name}.png')
    else:
        output_path = os.path.join(output_folder_path, f'{output_name}_{extra_text}.png')
    print(output_path)
    success = cv2.imwrite(output_path, debug_img)
    if not success:
        print(f'couldnt save')

def get_marked_regions(input_img: str, region_files: list[str], min_pixels: int, low_threshold: int,
                       high_threshold: int, debug: bool = False) -> list[str]:
    """
    Check which of the image regions defined in the region files contain marks in the input image. Region files
    and input_img must be same dimensions.
    :param input_img: The RGB image (not RGBA) to detect marks in.
    :param region_files: A list of RGB images (not RGBA) with sections marked in red pixels.
    :param min_pixels: The minimum number of pixels marked in a section for it to be counted as a marked section
    :param low_threshold: The low threshold for canny edge detection (not a colour threshold)
    :param high_threshold: The high threshold for canny edge detection (not a colour threshold)
    :param debug: Display debug information
    :return: A list of the region files that had more than min_pixel pixels marked in input_img
    """
    print(f'Image: {input_img}')
    src_img = cv2.imread(input_img)

    drawn_pixels = get_drawn_pixels(input_img, low_threshold, high_threshold, debug)
    if debug:
        print(f'Pixels in foreground: {drawn_pixels.size}')
        print(f'Nonzero in foreground: {np.count_nonzero(drawn_pixels)}')

    marked_sections = []
    for s in region_files:
        section_image = cv2.imread(s)
        section_mask = cv2.inRange(section_image, (0, 0, 255), (0, 0, 255))
        pixels_in_section = cv2.bitwise_and(src_img, src_img, mask=section_mask)

        if debug:
            print(f'Pixels in section {s}: {pixels_in_section.size}')
            print(f'Nonzero in section {s}: {np.count_nonzero(pixels_in_section)}')

        foreground_pixels_in_section = cv2.bitwise_and(pixels_in_section, pixels_in_section, mask=drawn_pixels)
        nonzero_pixels = np.count_nonzero(foreground_pixels_in_section)

        if debug:
            print(f'Pixels {s}: {foreground_pixels_in_section.size}')
            print(f'Nonzero {s}: {nonzero_pixels}')
        if nonzero_pixels > min_pixels:
            marked_sections.append(s)
    return marked_sections

def get_contours(image_path: str, low_threshold: int, high_threshold: int):
    """
    Detects the edges in the provided image, to find any lines.
    :param image_path: Image with drawn lines isolated. That is, the manikin outline should have already been removed.
    :param low_threshold: Lower bound of colour to treat as background colour, in
    :param high_threshold:
    :return: A 2D array of contours, where [0][0] is the yx coordinates of the first pixels of the first contour, and
    the shape of the array.
    """
    image = cv2.imread(image_path)

    if image is None:
        print(f'Could not open {image_path}')
        exit()

    # Convert image to gray and blur it
    src_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    src_gray = cv2.blur(src_gray, (3, 3))

    canny_output = cv2.Canny(src_gray, low_threshold, high_threshold)

    contours, _ = cv2.findContours(canny_output, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # contours has length of the number of contours
    # contours[0] is the first contour
    # contours[0][0] is the yx coordinates of the first pixel of the first contour
    return contours, canny_output.shape

def get_drawn_pixels(image_path: str, low_threshold: int, high_threshold: int,
                     debug: bool = False) -> np.ndarray:
    """
    Uses edge detection to get the drawn pixels ignoring small amounts of noise
    :param image_path: Location of image to get drawn pixels for
    :param low_threshold: Lower bound for canny edge detection threshold
    :param high_threshold: Upper bound for canny edge detection threshold
    :param debug: Show debug info
    :return: Array in same shape as input image, 0 if no pixels in that location and 1 if there are
    """
    contours, shape = get_contours(image_path, low_threshold, high_threshold)
    if debug:
        print(f'{len(contours)} contours found')

    drawing = np.zeros((shape[0], shape[1]), dtype=np.uint8)

    for i in range(len(contours)):
        cv2.drawContours(drawing, contours, i, 1)

    return drawing

def crop_to_mask(image_data, pixel_mask: list) -> np.ndarray:
    cropped_img = np.array([[255,255,255]]*len(image_data))
    for p in pixel_mask:
        pixel = image_data[p]
        cropped_img[p] = pixel
    return cropped_img

def get_pixel_locs(pixels, inclusion_colour: list[tuple[int, int, int]]) -> list:
    # todo remove this function
    pixel_mask = []
    for i in range(len(pixels)):
        if pixels[i] in inclusion_colour:
            pixel_mask.append(i)
    return pixel_mask

def pixel_average_from_list(images: list[str], override_num_images: int=-1) -> Image:
    num_images = len(images)
    print(f'Generating average of {num_images} images...')

    if override_num_images != -1:
        num_images = override_num_images

    running_average = np.zeros_like(Image.open(images[0]))
    for i in images:
        loaded_image = np.array(Image.open(i))
        proportional_image = np.divide(loaded_image, num_images)
        running_average = np.add(running_average, proportional_image)

    if override_num_images != -1:
        # override num images should always be more than num images
        # the purpose is to be able to compare two heatmaps where one had fewer examples
        # so we essentially add in a bunch of blank examples to the set with fewer examples
        diff = override_num_images - len(images)
        running_average = np.add(running_average, (255/override_num_images)*diff)

    img = Image.fromarray(running_average.astype(np.uint8))
    return img

def align_images(image, template, debug=False):
    # code based on https://pyimagesearch.com/2020/08/31/image-alignment-and-registration-with-opencv/
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    sift = cv2.SIFT_create()
    (keypoints_a, descriptors_a) = sift.detectAndCompute(image_gray, None)
    (keypoints_b, descriptors_b) = sift.detectAndCompute(template_gray, None)

    # match the features
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(descriptors_a, descriptors_b, k=2)
    good = []
    for m,n in matches:
        if m.distance < 0.75*n.distance:
            good.append(m)
    matches = good

    # check to see if we should visualize the matched keypoints
    if debug:
        matchedVis = cv2.drawMatches(image, keypoints_a, template, keypoints_b, matches, None)
        matchedVis = imutils.resize(matchedVis, width=1000)
        cv2.imshow("Matched Keypoints", matchedVis)
        cv2.waitKey(0)

    matched_points_a = np.zeros((len(matches), 2), dtype="float")
    matched_points_b = np.zeros((len(matches), 2), dtype="float")

    # loop over the top matches
    for (i, m) in enumerate(matches):
        # indicate that the two keypoints in the respective images
        # map to each other
        matched_points_a[i] = keypoints_a[m.queryIdx].pt
        matched_points_b[i] = keypoints_b[m.trainIdx].pt

    # compute the homography matrix between the two sets of matched points
    (homography_matrix, mask) = cv2.findHomography(matched_points_a, matched_points_b, method=cv2.RANSAC)

    # use the homography matrix to align the images
    (h, w) = template.shape[:2]
    aligned = cv2.warpPerspective(image, homography_matrix,  (w, h), borderMode=cv2.BORDER_REPLICATE)

    # return the aligned image
    return aligned

def get_template_mask(image_path: str, hsv_lower: tuple[int, int, int], hsv_upper: tuple[int, int, int], erosion_size: int):
    src_img = cv2.imread(image_path)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * erosion_size + 1, 2 * erosion_size + 1),
                                       (erosion_size, erosion_size))
    eroded_img = cv2.erode(src_img, kernel)

    # threshold eroded image to get only background colours
    mask = cv2.inRange(eroded_img, hsv_lower, hsv_upper)

    # invert mask to get only template line locations
    inverted_mask = cv2.bitwise_not(mask)
    return inverted_mask

def remove_light_pixels(image, hsv_lower, hsv_upper):
    mask = cv2.inRange(image, hsv_lower, hsv_upper)
    result = remove_template_pixels(image, hsv_upper, mask)
    return result

def demo_template_pixels(image_path: str, hsv_lower: tuple[int, int, int], hsv_upper: tuple[int, int, int], erosion_size: int):
    inverted_mask = get_template_mask(image_path, hsv_lower, hsv_upper, erosion_size)
    # show masked area: white lines will be blanked out
    show_image(inverted_mask, 'Masked area')

def remove_template_pixels(image, background_colour: tuple[int, int, int], template_mask):
    """
    Remove the pixels of the template mask from the input image
    :param image: raw aligned image
    :param background_colour: background colour to set template mask pixels to
    :param template_mask: Template mask from get_template_mask or get_mask function
    :return: input img with template mask pixels set to background colour
    """
    inverted_mask = cv2.bitwise_not(template_mask)

    foreground = cv2.bitwise_or(image, image, mask=inverted_mask)

    background = make_img_of_colour(image.shape, background_colour)
    masked_background = cv2.bitwise_or(background, background, mask=template_mask)

    combined = cv2.bitwise_or(foreground, masked_background)
    return combined

def get_mask(manikin_template_path: str, bgr_value: tuple[int, int, int]):
    template_image = cv2.imread(manikin_template_path)
    binary_mask = cv2.inRange(template_image, bgr_value, bgr_value)
    #invert pixels for compatibility with remove_template_pixels function
    inverted = cv2.bitwise_not(binary_mask)
    return inverted

def make_img_of_colour(shape: tuple[int, int], colour: tuple[int, int, int]) -> np.ndarray:
    background = np.zeros((shape[0], shape[1], 3), np.uint8)
    background[:] = colour
    return background

def apply_preprocessing_filters(input_img):
    """
    Takes input image and applies contrast filters to remove some noise
    :param input_img: aligned image with template mask pixels already removed
    :return: image with filters applied
    """
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(input_img, cv2.MORPH_OPEN, kernel)
    return opening

def get_alignment_rating(template_path: str, aligned_path: str,
                         hsv_lower: tuple[int, int, int], hsv_upper: tuple[int, int, int]):
    """
    Calculate a rating of how well the image saved in the aligned path has been aligned with the image in the
    template path. A rating of 1 indicates that the images have been perfectly aligned, a lower score indicates a
    poorer alignment.
    :param template_path: The path to the template that images were aligned to
    :param aligned_path: The path to the aligned image being checked
    :param hsv_lower: The lower bound of the background colour
    :param hsv_upper: The upper bound of the background colour
    :return: An alignment rating between 0 and 1, with 1 indicating perfect alignment.
    """
    template_img = cv2.imread(template_path)
    aligned_img = cv2.imread(aligned_path)

    # threshold images to get only background colours then invert to get only foreground pixels
    # inRange will set all pixels in the specified range to 255 and all others to 0
    template_mask = cv2.inRange(template_img, hsv_lower, hsv_upper)
    template_mask = cv2.bitwise_not(template_mask)

    aligned_mask = cv2.inRange(aligned_img, hsv_lower, hsv_upper)
    aligned_mask = cv2.bitwise_not(aligned_mask)

    # overlap mask will now have all pixels that are foreground in BOTH images set to 255, and all others set to 0
    # i.e. any pixel that is in the background colour range in either image will be set to 0
    overlap_mask = cv2.bitwise_and(template_mask, aligned_mask)

    # create dictionaries for the template mask and the overlap mask with the counts of the values 0 and 255
    unique, counts = np.unique(template_mask, return_counts=True)
    template_dict = dict(zip(unique, counts))

    unique, counts = np.unique(overlap_mask, return_counts=True)
    overlap_dict = dict(zip(unique, counts))

    # divide the number of foreground pixels in the overlap mask by the number of foreground pixels in the template mask
    # if the images were correctly aligned, all foreground pixels in the template mask will also be foreground pixels
    # in the overlap mask, giving an alignment rating of 1
    alignment_rating = overlap_dict[255]/template_dict[255]
    return alignment_rating

def get_distance_between_vectors(v1, v2) -> float:
    distances = []
    for x1 in v1:
        for x2 in v2:
            # for some reason each pair of points is wrapped in an extra list
            distances.append(math.dist(x1[0], x2[0]))

    return min(distances)

def get_contour_distance_matrix(contours) -> np.array:
    num_contours = len(contours)
    distance_matrix = np.zeros((num_contours, num_contours))
    for i in range(num_contours):
        ci = contours[i]
        for j in range(num_contours):
            cj = contours[j]
            distance_matrix[i][j] = get_distance_between_vectors(ci, cj)
    return distance_matrix

def fast_distance_matrix(contours) -> np.array:
    hull_list = []
    for i in range(len(contours)):
        hull = cv2.convexHull(contours[i])
        hull_list.append(hull)

    num_contours = len(contours)
    distance_matrix = np.zeros((num_contours, num_contours))
    for i in range(num_contours):
        ci = hull_list[i]
        for j in range(num_contours):
            cj = hull_list[j]
            distance_matrix[i][j] = get_distance_between_vectors(ci, cj)
    return distance_matrix

def agglomerative_clustering(contours):
    # group together nearby contours
    distance_matrix = get_contour_distance_matrix(contours)
    # Linkage method to use for hierarchical clustering. Can be average, complete, or single.
    # need a better way to determine num clusters
    n_clusters = 18
    a_g = AgglomerativeClustering(n_clusters=n_clusters, metric='precomputed', linkage='average')
    a_g.fit(distance_matrix)

    contours_dict = {}
    for i in range(len(contours)):
        l = a_g.labels_[i]
        if not l in contours_dict:
            contours_dict[l] = []
        contours_dict[l].append(contours[i])

    hull_list = []
    for k,v in contours_dict.items():
        cont = np.vstack([v[i] for i in range(len(v))])
        hull = cv2.convexHull(cont)
        hull_list.append(hull)
    return hull_list

def individual(contours):
    # Find the convex hull object for each contour
    hull_list = []
    for i in range(len(contours)):
        hull = cv2.convexHull(contours[i])
        hull_list.append(hull)
    return hull_list

def hierarchical_clustering(contours, threshold: int):
    """
    Cluster the provided sequence of contours and draw convex hulls around each cluster.
    :param contours:
    :param threshold: The threshold to use for clustering - higher threshold means bigger clusters.
    :return: The list of convex hulls drawn around each cluster.
    """
    distance_matrix = fast_distance_matrix(contours)
    condensed = sdistance.squareform(distance_matrix)
    linked = hcluster.linkage(condensed)
    clusters = hcluster.fcluster(linked, threshold, criterion='distance')
    contours_dict = {}
    for i in range(len(contours)):
        l = clusters[i]
        if not l in contours_dict:
            contours_dict[l] = []
        contours_dict[l].append(contours[i])

    hull_list = []
    for k,v in contours_dict.items():
        cont = np.vstack([v[i] for i in range(len(v))])
        hull = cv2.convexHull(cont)
        hull_list.append(hull)
    return hull_list


def get_convex_hull(image_path: str, low_threshold: int, high_threshold: int, output_dir: str,
                    clustering_threshold: int,
                    source_image: str = '', method: str = 'hierarchical',
                    debug:bool=False, debug_dir: str = '',
                    visualise:bool=True, vis_dir: str = '',
                    pixel_mask_template: str = ''):
    """

    :param image_path:
    :param low_threshold:
    :param high_threshold:
    :param output_dir: The directory to save pixel maps of found pain regions to.
    :param clustering_threshold: The threshold to use when clustering contours. Higher numbers will form bigger groups.
    :param debug: Whether to output images of found contours. If true, must specify debug_dir.
    :param source_image: If debug is true and a source image is provided, the convex hulls will be drawn onto the source
    image and saved to the debug folder.
    :param method:
    :param debug_dir: Must be specified if debug = True. The directory to save debug images to.
    :param visualise: Whether to output visualisation of convex hull drawn over original image. If True, must specify
    source_image and vis_dir
    :param vis_dir: The directory to save visualisations to.
    :param pixel_mask_template: The manikin pixel template
    :return:
    """
    contours, shape = get_contours(image_path, low_threshold, high_threshold)

    if debug:
        data_io.try_make_dir(debug_dir)
        debug_img = np.full((shape[0], shape[1], 3), 255, dtype=np.uint8)
        for i in range(len(contours)):
            cv2.drawContours(debug_img, contours, i, [0,0,0])
        debug_save(image_path, debug_dir, debug_img, 'drawn')

    if len(contours) == 0:
        return

    if method == 'agglomerative':
        hull_list = agglomerative_clustering(contours)
    elif method == 'hierarchical':
        hull_list = hierarchical_clustering(contours, clustering_threshold)
    else:
        hull_list = individual(contours)

    # output image (should be easily computer interpretable)
    blank_image = np.full((shape[0], shape[1], 3), 255, dtype=np.uint8)

    if visualise and source_image != '':
        # Draw contours + hull results over source image
        # todo add try catch in case source image path isn't valid, and default to blank
        drawing = cv2.imread(source_image)
        data_io.try_make_dir(vis_dir)
    else:
        visualise = False
        drawing = None

    data_io.try_make_dir(output_dir)

    for i in range(len(hull_list)):
        color = (0,0,255)
        # draw raw contours
        cv2.drawContours(blank_image, hull_list, i, color, thickness=-1)

        if visualise:
            cv2.drawContours(drawing, hull_list, i, color, thickness=5)

    if pixel_mask_template != '':
        mask = get_mask(pixel_mask_template, (0, 0, 255))
        # apply mask to remove pixels outside manikin boundary
        blank_image = remove_template_pixels(blank_image, (255,255,255), mask)

    debug_save(image_path, output_dir, blank_image)

    if visualise:
        debug_save(image_path, vis_dir, drawing, 'hulls')


def show_image(img, title):
    drawing = imutils.resize(img, width=1000)
    cv2.imshow(title, drawing)
    cv2.waitKey(0)
