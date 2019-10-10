My view of what I am trying to achieve with the json changes are:

layerProperties:
"MapFrame" - shows which map frame the data should be displayed in as line width, text size etc differs if in main map or location map
"LayerName" - simplified version of the MA naming convention, four elements i.e. mainmap-s0-pt-settlements
	1 - where the data should be displayed
	2 - scale it should be displayed at
	3 - data type i.e. pt, ln, py, ras etc
	4 - dataset
"RegExp" - the regular expression to find the relevant data
"DefinitionQuery" - if there are features which should be removed / kept
"Display" - is the data displayed. Mostly yes but sometimes, for data driven pages, they are not
"LabelClasses" - if the labels are to be different i.e. size etc

mapCookbook:
"mapnumber" - starting the idea of standardising the names of each map
	MA001-MA010 - Initial Reference maps
	MA011-MA020 - Initial Thematic maps
	MA041-MA060 - 3w maps
	MA061-MAnnn - Remaining maps
"category" - reference or thematic will be used to restrict map templates that are used
"product" - can be used as the title
"classification" - replaced with "category" and potential can be removed
"export" - yes or no, useful if want to automated export (when the orientation has been calculated, removes manual element). No for data driven pages as not 100% can be programmed
"layers" - the data that is loaded using the "LayerName" from the layerProperties json file

Future development:
I would like to add the following which would be used to populate the tags
"version" - initially always v01 but this may changes
"country" - outside of the recipes etc holding country name and ISO code
"glidenumber" - obvious
"projection" - obvious
"elements" - such as 'Reference' or '3www' etc which are 'tags' in ArcGIS