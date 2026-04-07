from digitisation import metrics
from digitisation import data_io

if __name__ == '__main__':
    print('PDF alignment:')
    metrics.get_alignment_stats(['data/synthetic/datafiles_pdf/alignment_log.csv'])

    matched_files = data_io.get_matching_files_dict('data/synthetic/manual_pixel_maps_masked', 'data/synthetic/output_pdf/pain_regions', '.png')
    metrics.calculate_dice_surface_distances(matched_files, 'data/synthetic/datafiles_pdf/dsc_tau5.csv', 5, verbose=False)
    metrics.get_file_summary_stats('data/synthetic/datafiles_pdf/dsc_tau5.csv', 'dsc')

    metrics.calculate_normalised_surface_distances(matched_files, 'data/synthetic/datafiles_pdf/nsd_tau5.csv', 5, verbose=False)
    metrics.get_file_summary_stats('data/synthetic/datafiles_pdf/nsd_tau5.csv', 'nsd')
    matched_files = data_io.get_matching_files_dict('data/synthetic/manual_pixel_maps_masked',
                                                    'data/synthetic/manual_pixel_maps_masked','.png')
    metrics.calculate_jaccard_indexes_lowmem(matched_files, 'data/synthetic/datafiles_pdf/jaccard_new.csv')
    metrics.get_file_summary_stats('data/synthetic/datafiles_pdf/jaccard_new.csv', 'jaccard')

    files_a = data_io.get_source_files('data/synthetic/manual_pixel_maps_masked', '.png')
    files_b = data_io.get_source_files('data/synthetic/output_pdf/pain_regions', '.png')
    metrics.calculate_jaccard_indexes(files_a, files_b, 'data/synthetic/datafiles_pdf/jaccard_old.csv')
    metrics.get_file_summary_stats('data/synthetic/datafiles_pdf/jaccard_old.csv', 'jaccard')
