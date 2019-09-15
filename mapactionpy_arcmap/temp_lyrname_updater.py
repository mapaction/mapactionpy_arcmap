import os

this_dir = os.path.abspath(os.path.dirname(__file__))
example_cookbook_path = os.path.join(this_dir, 'Config', 'mapCookbook.json')
example_lyr_props__path = os.path.join(this_dir, 'Config', 'layerProperties.json')

output_cookbook_path = os.path.join(this_dir, 'Config', 'mapCookbook.v2.json')
output_lyr_props__path = os.path.join(
    this_dir, 'Config', 'layerProperties.v2.json')


find_and_replace = [
    ('Elevation - Hillshade', 'mainmap-s0-ras-hillshade'),
    ('Transport - Airports', 'mainmap-s0-pt-airports'),
    ('Transport - Seaports', 'mainmap-s0-pt-seaports'),
    ('Admin 0 - Affected Country', 'mainmap-s0-py-affectedcountry'),
    ('Transport - Rail', 'mainmap-s0-ln-rail'),
    ('Physical - Sea', 'mainmap-s0-py-sea'),
    ('Admin - Ad 1 Polygon', 'mainmap-s0-py-admin1'),
    ('Admin - Ad 2 Polygon', 'mainmap-s0-py-admin2'),
    ('Elevation - Coastline', 'mainmap-s1-ln-coastline'),
    ('Transport - Roads', 'mainmap-s0-ln-roads'),
    ('Elevation - Curvature', 'mainmap-s0-ras-curvature'),
    ('Elevation - DEM', 'mainmap-s0-ras-dem'),
    ('Admin - Ad 4 Polygon', 'mainmap-s3-py-admin4'),
    ('Admin 0 - Surrounding Country', 'mainmap-s0-py-surroundingcountries'),
    ('Physical - Lakes', 'mainmap-s0-py-waterbodies'),
    ('Cartography - Feather', 'mainmap-s0-py-feather'),
    ('Borders - Admin 1', 'mainmap-s1-ln-admin1'),
    ('Borders - Admin 2', 'mainmap-s1-ln-admin2'),
    ('Admin - Ad 3 Polygon', 'mainmap-s2-py-admin3'),
    ('Settlements - Places', 'mainmap-s0-pt-settlements'),
    ('Physical - Rivers', 'mainmap-s0-ln-rivers'),
    ('Legend - Roads', 'legend-s0-ln-road'),
    ('Provinces', 'mainmap-s0-py-admin1'),
    ('Location - Surrounding Country', 'locationmap-s0-py-surroundingcountries'),
    ('Legend - Water', 'legend-s0-py-waterbodies'),
    ('Elevation - DEM EXCLUDE', 'mainmap-s0-ras-dem'),
    ('Borders - Admin 4', 'mainmap-s3-py-admin4'),
    ('Physical - Waterbodies', 'mainmap-s0-py-waterbodies'),
    ('Borders - Admin 3', 'mainmap-s2-ln-admin3'),
    ('229_stle', '228_stle'),
    ('229_stle', '228_stle'),
    ('232_tran', '230_tran'),
    ('221_phys', '220_phys'),
    ('223_popu', '222_popu')
]


def update_file(infilepath, outfilepath):
    with open(infilepath, 'r') as infile:
        s = infile.read()

    for find, replace in find_and_replace:
        s = s.replace(find, replace)

    with open(outfilepath, 'w') as outfile:
        outfile.write(s)


if __name__ == "__main__":
    update_file(example_cookbook_path, output_cookbook_path)
    update_file(example_lyr_props__path, output_lyr_props__path)
