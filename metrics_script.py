from digitisation import metrics

if __name__ == '__main__':
    print('PDF alignment:')
    metrics.get_alignment_stats(['data/datafiles_pdf/alignment_log.csv'])
