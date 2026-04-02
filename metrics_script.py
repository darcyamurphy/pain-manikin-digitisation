from digitisation import metrics
from digitisation import data_io

if __name__ == '__main__':
    print('PDF alignment:')
    metrics.get_alignment_stats(['data/synthetic/datafiles_pdf/alignment_log.csv'])

    matched_files = data_io.get_matching_files_dict('data/synthetic/manual_pixel_maps_masked', 'data/synthetic/output_pdf/pain_regions', '.png')
    metrics.calculate_dice_surface_distances(matched_files, 'data/synthetic/datafiles_pdf/dsc_tau5.csv', 5)