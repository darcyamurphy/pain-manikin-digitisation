from digitisation import metrics

if __name__ == '__main__':
    print('APMR alignment:')
    apmr_alignment_files = ['data/datafiles/alignment_log_1.csv', 'data/datafiles_2/alignment_log.csv']
    metrics.get_alignment_stats(apmr_alignment_files, 'pain')

    print('Synthetic (photograph) alignment')
    synthetic_alignment_files = ['data/synthetic/datafiles/alignment_log_1.csv']
    metrics.get_alignment_stats(synthetic_alignment_files)

    print('Synthetic (scanned) alignment')
    synthetic_scan_alignment_files = ['data/synthetic/datafiles_pdf/alignment_log_1.csv']
    metrics.get_alignment_stats(synthetic_scan_alignment_files)

    print('Cohen\'s kappa (APMR)')
    auto_apmr_regions = 'manual_annotation/datafiles/sections_20_fixed.csv'
    manual_apmr_regions = 'manual_annotation/dm-body-regions.csv'
    metrics.regions_cohens_kappa([manual_apmr_regions], [auto_apmr_regions], 'apmr')

    print('Cohen\'s kappa (synthetic scan/manual)')
    auto_synthetic_scan_regions = 'data/synthetic/datafiles_pdf/sections_20_fixed.csv'
    manual_synthetic_regions = 'data/synthetic/manual_annotation.csv'
    metrics.regions_cohens_kappa([auto_synthetic_scan_regions], [manual_synthetic_regions],
                                 'synthetic_scan_manual')

    print('Cohen\'s kappa (synthetic photograph/manual)')
    auto_synthetic_photo_regions = 'data/synthetic/datafiles/sections_20_fixed.csv'
    metrics.regions_cohens_kappa([auto_synthetic_photo_regions], [manual_synthetic_regions],
                                 'synthetic_photo_manual')

    print('Cohen\'s kappa (synthetic scan/photograph)')
    metrics.regions_cohens_kappa([auto_synthetic_scan_regions], [auto_synthetic_photo_regions],
                                 'synthetic_scan_photo')
