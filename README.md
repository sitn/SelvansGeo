# SelvansGeo
Spatial extension of the SELVANS information system - a forest managment application

This plugin is not generic and is designed for specific database structure dedicated
to forest surveys analysis and forest cadastre edition.


## For QGIS 2

For QGIS 2 serie please you the last 2.XX release
https://github.com/sitn/SelvansGeo/releases/tag/1.99.99 and copy the config and
project file to the usual location.

*IMPORTANT*: in order to have QGIS 2 accept to load the plugin, you must edit the
metadata.txt file and setup a correct qgisMinimumVersion tag.

There is also a legacy branch in this repository (version_28).

## For QGIS 3

The UI can be edited using QTDesigner that is shipped with QGIS standalone installation.
On windows, you'll usually find it following a path analog to:
`C:\Program Files\QGIS 2.99\apps\Qt5\bin\designer.exe`

Be sure to have the Python Script folder in your path in order to be able to use the
commands here under.

### Building UI for QGIS 3

If any changes are made to the UI, this one should be rebuilt using the following
commands:

    pyrcc5 -o resources.py resources.qrc
    pyuic5 -o ui_selvansgeo.py ui_selvansgeo.ui

To install pyQt 5, please read http://pyqt.sourceforge.net/Docs/PyQt5/installation.html
and use pip3 to do so.

## Configuration and default QGIS project

The configuration file (selvangeo.yaml) must be created and edited before starting the plugin

Simply fill the values here https://github.com/monodo/SelvansGeo/blob/qgis_3/selvansgeo.yaml_template,
rename the file to .yaml and reload the plugin

The default QGIS project must be copied in a qgisprj directory at plugin root level.

Example of analysis output: tree volume by hectare at last survey.

![Volume by hectare](/images/example.png?raw=true "Volume by hectare")

### Developer environment

To easily develop and link the plugin, one should consider creating a linked folder between
the QGIS Python plugin folder and the work/development folder. To do so, you
can use a symlink:

1. Create your working folder and link it to your Github repositories (something
like `c:/projects/selvansgeo`)
2. In the Python plugin folder of QGIS (if on Windows 64bits, it would be
somewhere like `C:\Program Files\QGIS 3.0\apps\qgis\python\plugins`,
create a new folder `selvansgeo`.
3. Open a command prompt as Administrator and run:

```
    mklink /D "c:\Program Files\QGIS 3.0\apps\qgis\python\plugins\selvansgeo" "c:\projects\selvansgeo"
```

Now you can develop in your working and tested it live in QGIS (using the plugin reloader).
