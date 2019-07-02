import arcpy
import argparse
import json
from shutil import copyfile
from layer_builder import LayerBuilder
from mapframe_builder import MapFrameBuilder


def update_map(self, mxd, datasources_dict):
    lb = LayerBuilder(arcpy.mapping.ListLayers(mxd))
    lb.set_datasource()

    # mfb = MapFrameBuilder()
    # mfb.do_stuff()
    # etc...
    #
    # end with this
    mxd.save()


def main(self, args):
    print (args)
    try:
        # open mxd
        copyfile(args.input_mxd, args.output_mxd)
        mxd = arcpy.mapping.MapDocument(args.output_mxd) 

        # depending on opions open datasource dictionary
        if args.datasource_dictionary == '-':
            # standard in
            datasources_dict = json.load(sys.stdin)
        elif args.datasource_dictionary[0] == '@':
            # open file (removing the `@`` symbol from the path)
            with open(args.datasource_dictionary[1:]) as f:
                datasources_dict = json.load(f)
        else:
            # assume that input is the json as a string
            datasources_dict = json.loads

        update_map(mxd, datasources_dict)

    except IOError:
        print "error"
    finally:
        print "tidying up"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='This component accepts a template MXD file, a list of the'
        'relevant datasets along with other information required to create an'
        'event specific instance of a map.'
    )
    parser.add_argument(
        'output_mxd',
        help='The absolute path where the output mxd file should be written'
    )  # positional, rather than option.
    parser.add_argument(
        '-i', '--input-mxd',
        help='The absolute path to the template MXD to be used as the basis'
        'for new products'
    )
    parser.add_argument(
        '-d', '--datasource-dictionary',
        help="A dictionary of key value pairs in json format\n"
             " can be passed as a string directly\n"
             " If prefixed with an `@` symbol a fully qualified path of a file"
             " containing the datasource dictionary should be provided.\n"
             " If a '-' character is passed, then the datasource-dictionary is"
             " read from stdin, assuming a json structure"
    )
    args = parser.parse_args()
    main(args)
