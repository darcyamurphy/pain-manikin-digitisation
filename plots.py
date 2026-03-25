import pandas as pd
import argparse
import seaborn as sns
import matplotlib.pyplot as plt


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--jaccard', help='csv file with jaccard index scores')
    parser.add_argument('-a', '--alignment', help='csv file with alignment scores')
    parser.add_argument('--jaccard2', help='optional csv file with second set of jaccard indices')
    parser.add_argument('--j1_label', help='label for points from first jaccard index file when plotting'
                                           'two sets of points', default='set 1')
    parser.add_argument('--j2_label', help='label for second set of jaccard index scores when plotting'
                                           'two sets of points', default='set 2')
    args = parser.parse_args()

    if args.jaccard2 is None:
        jaccard_vs_alignment(args.jaccard, args.alignment)
    else:
        two_jaccard_vs_alignment(args.jaccard, args.j1_label, args.jaccard2, args.j2_label, args.alignment)

