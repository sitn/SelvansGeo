# SelvansGeo
Spatial extension of the SELVANS information system - a forest managment application

This plugin is not generic and is designed for specific database structure dedicated
to forest surveys analysis and forest cadastre edition


## For QGIS 2

For QGIS 2 serie please you the last 2.XX release https://github.com/sitn/SelvansGeo/releases/tag/1.99.99 and copy the config and project file to the usual location

IMPORTANT: in order to have QGIS 2 accept to load the plugin, you must edit the metadata.txt file and setup a correct qgisMinimumVersion tag

## For QGIS 3

The UI can be edited using QTDesigner that is shipped with QGIS standalone installation.
On windows, you'll usually find it following a path analog to: C:\Program Files\QGIS 2.99\apps\Qt5\bin\designer.exe

### Building UI for QGIS 3

<ul>
  <li>pyrcc5 -o resources.py resources.qrc
  <li>pyuic5-o ui_selvansgeo.py ui_selvansgeo.ui
</ul>


To install pyQt 5, please read http://pyqt.sourceforge.net/Docs/PyQt5/installation.html

### Hint for windows users. 
Once installed using pip3, the UI compilation command will look like: 
C:\Python36\Scripts\pyuic5.exe -o ui_selvansgeo.py ui_selvansgeo.ui

## Configuration and default QGIS project

The configuration file (selvangeo.yaml) must be created and edited before starting the plugin

Simply fill the values here https://github.com/monodo/SelvansGeo/blob/qgis_3/selvansgeo.yaml_template,
rename the file to .yaml and reload the plugin

The default QGIS project must be copied in a qgisprj directory at plugin root level

Example of analysis output: tree volume by hectare at last survey

![Volume by hectare](/images/example.png?raw=true "Volume by hectare")
