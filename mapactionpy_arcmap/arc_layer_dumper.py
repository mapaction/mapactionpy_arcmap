import argparse
import os
import arcpy

# TODO: asmith 2020/03/03
# What is the purpose of this file? Is this a tool that is just used within the
# maintainance of the `default_crash_move_folder`? It's entirely legitimate if it
# is, but it would be interesting to consider whether it could be intergrated into
# the other tools better. For example could we dump the layer files to text files on
# each commit of the `default_crash_move_folder` and keep the output within the git
# repo. This would mean to would be easier to see *what* had changed when a binary
# layer file changes.


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


def get_layer_properties(file):
    lyr = arcpy.mapping.Layer(file)
    layerName = lyr.name.encode('utf-8').strip()

    if lyr.supports("DEFINITIONQUERY"):
        dq = lyr.definitionQuery.encode('utf-8').strip()
    else:
        dq = ""

    lblclassNames = []
    lblexpressions = []
    lblsql = []
    lblshow = False

    if lyr.supports("LABELCLASSES"):
        lblshow = lyr.showLabels
        for lblClass in lyr.labelClasses:
            if lblClass.showClassLabels:
                lblclassNames.append(lblClass.className.encode(
                    'utf-8').strip())
                lblexpressions.append(lblClass.expression.encode(
                    'utf-8').strip())
                lblsql.append(lblClass.SQLQuery.encode('utf-8').strip())

    return (layerName, dq, lblshow, lblclassNames, lblexpressions, lblsql)


def main(args):
    args = parser.parse_args()
    layerDirectory = args.layerDirectory

    # r=root, d=directories, f = files
    lyr_details = {}
    for r, d, f in os.walk(layerDirectory):
        for file in f:
            if '.lyr' in file:
                props = get_layer_properties(os.path.join(r, file))
                lyr_details[file] = props

    # Print one row per file:
    print("One row per file")
    print("fullPath|layerName|definitionQuery|lblshow|labelClassNameCount")
    for file in lyr_details:
        layerName, dq, lblshow, lblclassNames, lblexpressions, lblsql = lyr_details[file]
        print("|".join(map(str, (file, layerName, dq, lblshow, len(lblclassNames)))))

    print
    print
    print
    print("Only show files with Label Classes enabled and one row per *Label Class*")
    # Print one row per file:
    print("fullPath|layerName|definitionQuery|lblshow|labelClassNameCount|labelClassExpression|labelClassSQLQuery|")
    for file in lyr_details:
        layerName, dq, lblshow, lblclassNames, lblexpressions, lblsql = lyr_details[file]
        if len(lblclassNames):
            for n, e, s in zip(lblclassNames, lblexpressions, lblsql):
                print("|".join((file, layerName, dq, str(lblshow), n, e, s)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        # TODO: asmith 2020/03/03
        # presumably "layer files" not "later files"?
        description='Dumps the contents of later files.',
    )
    parser.add_argument("-ld", "--layerDirectory", dest="layerDirectory", required=True,
                        help="path to layer directory", metavar="FILE", type=lambda x: is_valid_directory(parser, x))
    args = parser.parse_args()
    main(args)
