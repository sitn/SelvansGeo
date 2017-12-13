# SelvansGeo
Spatial extension of the SELVANS information system - a forest managment application

This plugin is not generic and is designed for specific database structure dedicated
to forest surveys analysis and forest cadastre edition

For QGIS 2.18 LTR & QGIS 3

Building UI for QGIS 2.18:
<ul>
  <li>pyrcc4 -o resources_qgis2.py resources.qrc
  <li>pyuic4 -o ui_selvansgeo_qgis2.py ui_selvansgeo.ui
</ul>

To install pyQt 4, please read http://pyqt.sourceforge.net/Docs/PyQt4/installation.html

Building UI for QGIS 3
<ul>
  <li>pyrcc5 -o resources.py resources.qrc
  <li>pyuic5-o ui_selvansgeo.py ui_selvansgeo.ui
</ul>

To install pyQt 5, please read http://pyqt.sourceforge.net/Docs/PyQt5/installation.html

The configuration file (selvangeo.yaml) must be created before starting the plugin

Simply fill the values here https://github.com/monodo/SelvansGeo/blob/qgis_3/selvansgeo.yaml_template,
rename the file to .yaml and reload the plugin

Example of analysis output: tree volume by hectare at last survey

![Volume by hectare](/images/example.png?raw=true "Volume by hectare")
