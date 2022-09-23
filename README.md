# SelvansGeo
Spatial extension of the SELVANS information system - a forest managment application

This plugin is not generic and is designed for specific database structure dedicated
to forest surveys analysis and forest cadastre edition.

## QGIS 3 and QTDesigner

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

You do not need to install pyQT as it is already installed with QGIS
(C:\Program Files\QGIS 3.22.3\apps\Python39\Scripts)

To use these commands, you need to open an cmd and define all the needed
environment variables

You can inspire ourself with the following file:
C:\Program Files\QGIS 3.22.3\bin\qgis.bat

This one sets all the needed variables, just get rid of the last line
in order not to start QGIS.

Most important, do not modify this file!! Copy it and create another one.

## Configuration and default QGIS project

The configuration file (selvangeo.yaml) must be created and edited before starting the plugin

Simply fill the values here https://github.com/sitn/SelvansGeo/blob/master/selvansgeo.yaml_template,
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
somewhere like `C:\Program Files\QGIS 3.0\apps\qgis\python\plugins`.
3. Open a command prompt as Administrator and run:

```
    mklink /D "c:\Program Files\QGIS 3.0\apps\qgis\python\plugins\selvansgeo" "c:\projects\selvansgeo"
```

Now you can develop in your working and tested it live in QGIS (using the plugin reloader).

## Deployment

First run the deployment script:

```
    .\scripts\deploy.ps1
```

Then copy the created file to the QGIS plugin repository.

Do not forget to edit the qgis plugin XML to add the new created
version.
