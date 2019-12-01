import argparse
import os
from arcmap_runner import ArcMapRunner


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
        return False
    else:
        return arg


def is_valid_directory(parser, arg):
    if os.path.isdir(arg):
        return arg
    else:
        parser.error("The directory %s does not exist!" % arg)
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='This component accepts a template MXD file, a list of the'
        'relevant datasets along with other information required to create an'
        'event specific instance of a map.',
    )
    parser.add_argument("-b", "--cookbook", dest="cookbookFile", required=False,
                        help="path to cookbook json file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-l", "--layerConfig", dest="layerConfig", required=False,
                        help="path to layer config json file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-t", "--template", dest="templateFile", required=False,
                        help="path to MXD file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-cmf", "--cmf", dest="crashMoveFolder", required=True,
                        help="path the Crash Move Folder", metavar="FILE",
                        type=lambda x: is_valid_directory(parser, x))
    parser.add_argument("-ld", "--layerDirectory", dest="layerDirectory", required=False,
                        help="path to layer directory", metavar="FILE",
                        type=lambda x: is_valid_directory(parser, x))
    parser.add_argument("-p", "--product", dest="productName", required=True,
                        help="Name of product")
    parser.add_argument("-c", "--country", dest="countryName", required=False,
                        help="Name of country")
    args = parser.parse_args()

    runner = ArcMapRunner(args.cookbookFile,
                          args.layerConfig,
                          args.templateFile,
                          args.crashMoveFolder,
                          args.layerDirectory,
                          args.productName,
                          args.countryName)
    runner.generate()
