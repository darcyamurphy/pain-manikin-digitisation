from digitisation import metrics
from digitisation import data_io

if __name__ == '__main__':
    # can change these to true after running once if you just want to output results
    skip_synthetic_pdfs = False
    skip_synthetic_jpgs = False
    skip_synthetic_jpgs_200 = False
    skip_apmr = False

    if not skip_synthetic_pdfs:
        print('Processing synthetic pdf results')
        ## synthetic pdf metrics
        synthetic_pdf_matched_files = data_io.get_matching_files_dict('data/synthetic/manual_pixel_maps_masked',
                                                                      'data/synthetic/output_pdf/pain_regions',
                                                                      '.png')

        # normalised surface distance
        metrics.calculate_normalised_surface_distances(synthetic_pdf_matched_files,
                                                       'data/synthetic/datafiles_pdf/nsd_tau5.csv',
                                                       5, verbose=False)

        # overall pixel-wise jaccard index
        metrics.calculate_jaccard_indexes_lowmem(synthetic_pdf_matched_files,
                                                 'data/synthetic/datafiles_pdf/jaccard.csv', verbose=False)

        # per-region pixel-wise jaccard index
        region_maps = data_io.get_source_files('data/resources/widespreadpain_sections', '.png')
        metrics.per_region_jaccard_csv(synthetic_pdf_matched_files,
                                       'data/synthetic/datafiles_pdf/per_region_jaccard.csv',
                                       region_maps, 10, False)
        metrics.convert_per_region_jaccard_to_avg('data/synthetic/datafiles_pdf/per_region_jaccard.csv',
                                                  'data/synthetic/datafiles_pdf/per_region_jaccard_heatmap.csv',
                                                  region_maps)

        # body-region based jaccard index
        metrics.body_region_jaccard_index('data/synthetic/manual_annotation.csv',
                                          'data/synthetic/datafiles_pdf/body_region_annotations.csv',
                                          'data/synthetic/datafiles_pdf/body_region_jaccard.csv', verbose=False)

    if not skip_synthetic_jpgs:
        print('Processing synthetic photograph results')
        ## synthetic photograph metrics
        synthetic_jpg_matched_files = data_io.get_matching_files_dict('data/synthetic/manual_pixel_maps_masked',
                                                                      'data/synthetic/output_jpgs/pain_regions',
                                                                      '.png')

        # normalised surface distance
        metrics.calculate_normalised_surface_distances(synthetic_jpg_matched_files,
                                                       'data/synthetic/datafiles_jpgs/nsd_tau5.csv',
                                                       5, verbose=False)

        # overall pixel-wise jaccard index
        metrics.calculate_jaccard_indexes_lowmem(synthetic_jpg_matched_files,
                                                 'data/synthetic/datafiles_jpgs/jaccard.csv', verbose=False)

        # per-region pixel-wise jaccard index
        region_maps = data_io.get_source_files('data/resources/widespreadpain_sections', '.png')
        metrics.per_region_jaccard_csv(synthetic_jpg_matched_files,
                                       'data/synthetic/datafiles_jpgs/per_region_jaccard.csv',
                                       region_maps, 10, False)
        metrics.convert_per_region_jaccard_to_avg('data/synthetic/datafiles_jpgs/per_region_jaccard.csv',
                                                  'data/synthetic/datafiles_jpgs/per_region_jaccard_heatmap.csv',
                                                  region_maps)

        # body-region based jaccard index
        metrics.body_region_jaccard_index('data/synthetic/manual_annotation.csv',
                                          'data/synthetic/datafiles_jpgs/body_region_annotations.csv',
                                          'data/synthetic/datafiles_jpgs/body_region_jaccard.csv', verbose=False)

    if not skip_synthetic_jpgs_200:
        print('Processing synthetic photograph results (200 threshold)')
        ## synthetic photograph metrics
        synthetic_jpg_matched_files = data_io.get_matching_files_dict('data/synthetic/manual_pixel_maps_masked',
                                                                      'data/synthetic/output_jpgs_200/pain_regions',
                                                                      '.png')

        # normalised surface distance
        metrics.calculate_normalised_surface_distances(synthetic_jpg_matched_files,
                                                       'data/synthetic/datafiles_jpgs_200/nsd_tau5.csv',
                                                       5, verbose=False)

        # overall pixel-wise jaccard index
        metrics.calculate_jaccard_indexes_lowmem(synthetic_jpg_matched_files,
                                                 'data/synthetic/datafiles_jpgs_200/jaccard.csv', verbose=False)

        # per-region pixel-wise jaccard index
        region_maps = data_io.get_source_files('data/resources/widespreadpain_sections', '.png')
        metrics.per_region_jaccard_csv(synthetic_jpg_matched_files,
                                       'data/synthetic/datafiles_jpgs_200/per_region_jaccard.csv',
                                       region_maps, 10, False)
        metrics.convert_per_region_jaccard_to_avg('data/synthetic/datafiles_jpgs_200/per_region_jaccard.csv',
                                                  'data/synthetic/datafiles_jpgs_200/per_region_jaccard_heatmap.csv',
                                                  region_maps)

        # body-region based jaccard index
        metrics.body_region_jaccard_index('data/synthetic/manual_annotation.csv',
                                          'data/synthetic/datafiles_jpgs_200/body_region_annotations.csv',
                                          'data/synthetic/datafiles_jpgs_200/body_region_jaccard.csv', verbose=False)

    if not skip_apmr:
        print('Processing apmr results')
        ## apmr metrics
        apmr_matched_files = data_io.get_matching_files_dict('../manikin_data/apmr/manual_annotation/DM/masked_annotations',
                                                                      '../manikin_data/apmr/output/pain_regions',
                                                                      '.png')

        # normalised surface distance
        metrics.calculate_normalised_surface_distances(apmr_matched_files,
                                                       '../manikin_data/apmr/datafiles/nsd_tau5.csv',
                                                       5, verbose=False)

        # overall pixel-wise jaccard index
        metrics.calculate_jaccard_indexes_lowmem(apmr_matched_files,
                                                 '../manikin_data/apmr/datafiles/jaccard.csv', verbose=False)

        # per-region pixel-wise jaccard index
        region_maps = data_io.get_source_files('data/resources/widespreadpain_sections', '.png')
        metrics.per_region_jaccard_csv(apmr_matched_files,
                                       '../manikin_data/apmr/datafiles/per_region_jaccard.csv',
                                       region_maps, 10, False)
        metrics.convert_per_region_jaccard_to_avg('../manikin_data/apmr/datafiles/per_region_jaccard.csv',
                                                  '../manikin_data/apmr/datafiles/per_region_jaccard_heatmap.csv',
                                                  region_maps)

        # body-region based jaccard index
        metrics.body_region_jaccard_index('../manikin_data/apmr/manual_annotation/DM/dm-body-regions.csv',
                                          '../manikin_data/apmr/datafiles/body_region_annotations.csv',
                                          '../manikin_data/apmr/datafiles/body_region_jaccard.csv', verbose=False)


    print('--Synthetic pdf results--')
    print('Alignment:')
    metrics.get_alignment_stats(['data/synthetic/datafiles_pdf/alignment_log.csv'])
    print('Normalised Surface Distance')
    metrics.get_file_summary_stats('data/synthetic/datafiles_pdf/nsd_tau5.csv', 'nsd')
    print('Pixel-wise Jaccard')
    metrics.get_file_summary_stats('data/synthetic/datafiles_pdf/jaccard.csv', 'jaccard')
    print('Average per-region pixel-wise Jaccard')
    metrics.get_file_summary_stats('data/synthetic/datafiles_pdf/per_region_jaccard_heatmap.csv',
                                   'value', index_column='path')
    print('Body-region-based Jaccard')
    metrics.get_file_summary_stats('data/synthetic/datafiles_pdf/body_region_jaccard.csv', 'jaccard')

    print('--Synthetic jpg results (default colour thresholds)--')
    print('Alignment:')
    metrics.get_alignment_stats(['data/synthetic/datafiles_jpgs/alignment_log.csv'])
    print('Normalised Surface Distance')
    metrics.get_file_summary_stats('data/synthetic/datafiles_jpgs/nsd_tau5.csv', 'nsd')
    print('Pixel-wise Jaccard')
    metrics.get_file_summary_stats('data/synthetic/datafiles_jpgs/jaccard.csv', 'jaccard')
    print('Average per-region pixel-wise Jaccard')
    metrics.get_file_summary_stats('data/synthetic/datafiles_jpgs/per_region_jaccard_heatmap.csv',
                                   'value', index_column='path')
    print('Body-region-based Jaccard')
    metrics.get_file_summary_stats('data/synthetic/datafiles_jpgs/body_region_jaccard.csv', 'jaccard')

    print('--Synthetic jpg results (colour threshold 200)--')
    print('Alignment:')
    metrics.get_alignment_stats(['data/synthetic/datafiles_jpgs_200/alignment_log.csv'])
    print('Normalised Surface Distance')
    metrics.get_file_summary_stats('data/synthetic/datafiles_jpgs_200/nsd_tau5.csv', 'nsd')
    print('Pixel-wise Jaccard')
    metrics.get_file_summary_stats('data/synthetic/datafiles_jpgs_200/jaccard.csv', 'jaccard')
    print('Average per-region pixel-wise Jaccard')
    metrics.get_file_summary_stats('data/synthetic/datafiles_jpgs_200/per_region_jaccard_heatmap.csv',
                                   'value', index_column='path')
    print('Body-region-based Jaccard')
    metrics.get_file_summary_stats('data/synthetic/datafiles_jpgs_200/body_region_jaccard.csv', 'jaccard')


    print('--APMR results--')
    print('Alignment:')
    metrics.get_alignment_stats(['../manikin_data/apmr/datafiles/alignment_log.csv'])
    print('Normalised Surface Distance')
    metrics.get_file_summary_stats('../manikin_data/apmr/datafiles/nsd_tau5.csv', 'nsd')
    print('Pixel-wise Jaccard')
    metrics.get_file_summary_stats('../manikin_data/apmr/datafiles/jaccard.csv', 'jaccard')
    print('Average per-region pixel-wise Jaccard')
    metrics.get_file_summary_stats('../manikin_data/apmr/datafiles/per_region_jaccard_heatmap.csv',
                                   'value', index_column='path')
    print('Body-region-based Jaccard')
    metrics.get_file_summary_stats('../manikin_data/apmr/datafiles/body_region_jaccard.csv', 'jaccard')