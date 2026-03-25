import os
from . import data_io
import pandas as pd
import math
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats as st

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

def regions_cohens_kappa(rater_a_files: list[str], rater_b_files: list[str], file_prefix: str):
    """
    Rater a and Rater b should have rated the same files. The files must have a filename column and all other columns
    should be the variables rated as true or false. The filename column will be treated as the index.
    Takes lists of files rather than just the path to one file in case ratings are spread across multiple files
    :param rater_a_files: List of files containing rater a's ratings
    :param rater_b_files: List of files containing rater b's ratings
    :param file_prefix: prefix to use for log files
    :return:
    """
    df_a = get_full_df(rater_a_files).set_index('filename').sort_index().astype(str)
    df_b = get_full_df(rater_b_files).set_index('filename').sort_index().astype(str)
    # columns need to be in same order for compare
    df_b = df_b.reindex(columns=df_a.columns)

    try:
        diff_df = df_a.compare(df_b, keep_shape=True)
    except ValueError:
        print(ValueError)
        print(df_a)
        print(df_b)
        return

    # first create list of disagreements for qualitative analysis
    rater_a_vals = diff_df.xs('self', axis=1, level=1)
    rater_a_vals.to_csv(f'{file_prefix}_rater_a_vals.csv')
    print(f'saved disagreements to {file_prefix}_rater_a_vals.csv')
    rater_a_vals.notna().sum().to_csv(f'{file_prefix}_disagreements_by_col.csv')
    print(f'saved disagreements by column to {file_prefix}_disagreements_by_col.csv')

    # taking rater_a as correct for purpose of defining false positives etc
    # print out some extra stats
    false_positive = {}
    false_negative = {}
    fp_count = 0
    fn_count = 0
    for c in rater_a_vals.columns:
        result = rater_a_vals[c].value_counts()
        if 'False' in result.index:
            false_positive[c] = result['False']
            fp_count += result['False']
        if 'True' in result.index:
            false_negative[c] = result['True']
            fn_count += result['True']
    print(f'False positives (rater a as ground truth): {false_positive}')
    print(f'False negatives (rater a as ground truth): {false_negative}')

    # calculate pe
    total_columns = len(df_a.columns)
    total_rows = len(df_a)
    total_cells = total_columns * total_rows
    total_disagreements = rater_a_vals.notna().sum().sum()
    disagreement_rate = total_disagreements/total_cells
    print(f'Disagreement rate: {disagreement_rate}')

    # for each category need to know number of times each rater predicted it
    sum_k = 0
    for c in df_a.columns:
        a_counts = df_a[c].value_counts()
        if 'True' in a_counts:
            nk1 = a_counts['True']
        else:
            nk1 = 0

        b_counts = df_b[c].value_counts()
        if 'True' in b_counts:
            nk2 = b_counts['True']
        else:
            nk2 = 0
        sum_k += nk1
        sum_k += nk2

    pe = (1/total_cells**2)*sum_k
    print(f'sum_k: {sum_k} pe: {pe}')

    # calculate po
    total_agreement = total_cells - total_disagreements
    po = total_agreement/total_cells
    print(f'Agreement rate (po): {po}')

    # calculate k
    k = (po-pe)/(1-pe)
    print(f'Cohen\'s kappa: {k}')

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
