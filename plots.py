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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--jaccard', help='csv file with jaccard index scores')
    parser.add_argument('-a', '--alignment', help='csv file with alignment scores')
    args = parser.parse_args()
    jaccard_vs_alignment(args.jaccard, args.alignment)

