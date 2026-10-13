from digitisation import data_io
from digitisation import metrics
from digitisation import image_processing
import argparse
import configparser
import os

def run():
    parser = argparse.ArgumentParser()

    parser.add_argument('-j', '--jaccard', nargs=2,
                        help='Calculate jaccard index between files in two directories. All files in'
                             'first directory specified must have a file with matching name in second directory.'
                             'Output is stored in file specified in datafile arg')
    parser.add_argument('--jaccard_metrics', action='store_true',
                        help='Output stats on jaccard metrics in file specified in datafile arg')
    parser.add_argument('--datafile',
                        help='Specify file path to use when reading or writing to datafile')
    parser.add_argument('-x', '--extent',
                        help='Calculate pixel pain extents of files in specified dir and write to datafile')
    parser.add_argument('--rextent',
                        help='Calculate region pain extents from the body region annotations in the specified file'
                             ' and write to datafile.')
    parser.add_argument('--cextent', nargs=2,
                        help='Compare pain extents of first and second specified file')
    parser.add_argument('--heatmap',
                        help='Create heatmap of files in specified dir and save to datafile')
    parser.add_argument('--heatmap_num_override',
                        help='Override the actual number of images when weighting images for heatmap. Can be used'
                             'to harmonise heatmaps when one has less images than the other.')
    parser.add_argument('--extension', default='.png',
                        help='Override .png as the default extension to search directory for.')
    parser.add_argument('--file_list',
                        help='Specify a file with a list of source files to override searching default input dir')
    parser.add_argument('--config', help='Specify non-default config file', default='resources/metrics_config')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    if args.jaccard:
        jaccard_a, jaccard_b = args.jaccard
        files_a = data_io.get_source_files(jaccard_a, '.png')
        files_b = []
        for f in files_a:
            files_b.append(data_io.get_matched_file(f, jaccard_b))
        metrics.calculate_jaccard_indexes(files_a, files_b, args.datafile)

    if args.jaccard_metrics:
        metrics.get_file_summary_stats(args.datafile, 'jaccard')

    if args.extent:
        files = data_io.get_source_files(args.extent, args.extension)
        extent_template = config['RESOURCES']['PixelTemplate']
        metrics.get_pixel_pain_extents(files, extent_template, args.datafile)

    if args.rextent:
        region_files = data_io.get_source_files(config['RESOURCES']['RegionsDir'], '.png')
        metrics.get_body_region_pain_extent(args.rextent, region_files, config['RESOURCES']['PixelTemplate'],
                                            args.datafile)

    if args.cextent:
        datafile_a, datafile_b = args.cextent
        metrics.compare_pain_extents(datafile_a, datafile_b)

    if args.heatmap is not None:
        if args.heatmap_num_override is not None:
            heatmap_num = int(args.heatmap_num_override)
        else:
            heatmap_num = -1

        files = data_io.get_source_files(args.heatmap, args.extension)
        avg = image_processing.pixel_average_from_list(files, heatmap_num)
        avg.save(args.datafile)

if __name__ == '__main__':
    run()