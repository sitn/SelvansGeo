# -*- coding: utf-8 -*-

from builtins import str
from builtins import object
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QProgressBar
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProject, QgsVectorLayer, QgsMarkerSymbol
from qgis.core import QgsSingleSymbolRenderer, QgsRectangle
from qgis.core import QgsFeatureRequest, QgsFeature, QgsGeometry, QgsPoint

"""
Selvans custom cartographic tools
"""


class CartoTools(object):

    def __init__(self, iface, dlg):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.layerRegistry = QgsProject.instance()
        self.dlg = dlg
        self.messageBar = iface.messageBar()

    def showNodes(self):
        """
        Parse the geometry of a selected layer and show its vertices (nodes)
        """

        mr = self.layerRegistry
        # Get the selected layer for which to show nodes
        selectedIndex = self.dlg.comboLayers.currentIndex()
        selectedLayer = self.dlg.comboLayers.itemData(selectedIndex)
        registeredLayers = self.layerRegistry.mapLayersByName('Noeuds')
        featuresCount = int(selectedLayer.featureCount())

        # Remove the node layer if already existing
        if mr.mapLayersByName('Noeuds'):
            mr.removeMapLayer(mr.mapLayersByName('Noeuds')[0].id())

        # Create memory layer to display nodes
        self.nodeLayer = QgsVectorLayer("Point?crs=EPSG:2056",
                                        "Noeuds",
                                        "memory")

        self.nodeLayerProvider = self.nodeLayer.dataProvider()

        # Create rendering style
        nodeSymbol = QgsMarkerSymbol.defaultSymbol(
            self.nodeLayer.geometryType())

        nodeSymbol.setColor(QColor('#CC3300'))
        nodeSymbol.setSize(2.0)
        nodeRenderer = QgsSingleSymbolRenderer(nodeSymbol)
        self.nodeLayer.setRendererV2(nodeRenderer)

        # Select features visible in current map canvas extent
        if self.dlg.chkSelectByCanvasExtent.checkState():
            extent = self.canvas.extent()

            rect = QgsRectangle(extent.xMinimum(),
                                extent.yMinimum(),
                                extent.xMaximum(),
                                extent.yMaximum())

            request = QgsFeatureRequest()
            request.setFilterRect(rect)
            featureIterator = selectedLayer.getFeatures(request)

        # Select all features
        else:
            featureIterator = selectedLayer.getFeatures()

        # Create progress bar
        progressMessageBar = self.messageBar.createMessage(
            str("Création des noeuds...", "utf-8"))
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(featuresCount)
        progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        self.messageBar.pushWidget(progressMessageBar,
                                   self.iface.messageBar().INFO)

        # Iterate over feature
        k = 0
        for feature in featureIterator:
            k += 1
            progress.setValue(k)
            geom = feature.geometry()
            feat = QgsFeature()

            # Adapt procedure for each geometry type
            if(geom):
                type = geom.wkbType()
            # LineString
            if type == QGis.WKBLineString:
                for point in geom.asPolyline():
                    feat.setGeometry(QgsGeometry.fromPoint(point))
                    self.nodeLayerProvider.addFeatures([feat])
            # MultiLineString
            elif type == QGis.WKBMultiLineString:
                for line in geom.asMultiPolyline():
                    for vertex in line:
                        feat.setGeometry(
                            QgsGeometry.fromPoint(
                                QgsPoint(vertex[0], vertex[1])
                            )
                        )
                        self.nodeLayerProvider.addFeatures([feat])
            # Polygon
            elif type == QGis.WKBPolygon:
                polygons = geom.asPolygon()
                for polygon in polygons:
                    for vertex in polygon:
                        feat.setGeometry(QgsGeometry.fromPoint(
                            QgsPoint(vertex[0], vertex[1]))
                        )
                        self.nodeLayerProvider.addFeatures([feat])
            # MultiPolygon
            elif type == QGis.WKBMultiPolygon:
                multiPoly = geom.asMultiPolygon()
                for polygons in multiPoly:
                    for polygon in polygons:
                        for vertex in polygon:
                            feat.setGeometry(
                                QgsGeometry.fromPoint(
                                    QgsPoint(vertex[0], vertex[1])
                                )
                            )
                            self.nodeLayerProvider.addFeatures([feat])
            else:
                self.messageBar.pushMessage("Cartotools : ",
                                            str("Type de géométrie non" +
                                                    "supporté: " + str(type),
                                                    "utf-8"),
                                            level=QgsMessageBar.CRITICAL)

        self.messageBar.clearWidgets()

        self.layerRegistry.addMapLayer(self.nodeLayer)

    def clearNodeLayer(self):

        if self.layerRegistry.mapLayersByName('Noeuds'):
            self.layerRegistry.removeMapLayer(
                self.layerRegistry.mapLayersByName('Noeuds')[0].id()
            )
