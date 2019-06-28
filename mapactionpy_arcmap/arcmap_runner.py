
def main(args):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='This component accepts a template MXD file, a list of the'
        'relevant datasets along with other information required to create an'
        'event specific instance of a map.',
        formatter_class=SmartFormatter
    )
    parser.add_argument(
        'output_mxd_path'
        help='The absolute path where the output mxd file should be written'
    )  # positional, rather than option.
    parser.add_argument(
        '-i', '--input-mxd-path',
        help='The absolute path to the template MXD to be used as the basis'
        'for new products'
    )
    parser.add_argument(
        '-d', '--dataset-dictionary',
        help="A dictionary of key value pairs in json format"
    )
    args = parser.parse_args()
    main(args)
