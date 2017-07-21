# -*- coding: utf-8 -*-

from builtins import str
from builtins import object
from qgis.PyQt.QtWidgets import QListWidgetItem


class tabularNavigation(object):

    def __init__(self,
                 dlg,
                 pgdb,
                 canvas,
                 iface):

        self.dlg = dlg
        self.pgdb = pgdb
        self.canvas = canvas
        self.messageBar = iface.messageBar()
        self.fillArr()

    def fillArr(self):
        """
        Fill the arrondissements list (first geographic level)
        """
        arrLayer = self.pgdb.getLayer("parcellaire",
                                      "arrondissements",
                                      "geom",
                                      "",
                                      "listArr",
                                      "idobj")

        features = arrLayer.getFeatures()
        i = 0
        nameList = []
        for feature in features:
            i += 1
            attrs = feature.attributes()
            idx = arrLayer.fields().indexFromName("nom")
            name = attrs[idx]
            idx = arrLayer.fields().indexFromName("numero")
            numero = attrs[idx]
            if name not in nameList:
                nameList.append(name)
                self.dlg.listArr.addItem(
                    QSelvansListItem(
                        numero,
                        name,
                        feature.geometry().boundingBox()
                    )
                )

    def selectAdministration(self, item):
        """
        Select Administrations belonging to clicked arrondissement
        """
        self.dlg.listAdm.clear()
        self.dlg.listDiv.clear()
        whereClause = " arrdt = '" + str(item.itemId) + "'"
        admLayer = self.pgdb.getLayer("parcellaire",
                                      "administrations",
                                      "geom",
                                      whereClause,
                                      "listAdm",
                                      "idobj")
        features = admLayer.getFeatures()
        i = 0

        nameList = []
        for feature in features:
            i += 1
            attrs = feature.attributes()
            idx = admLayer.fields().indexFromName("adm")
            adm = attrs[idx]
            idx = admLayer.fields().indexFromName("codeadm")
            codeadm = attrs[idx]
            self.dlg.listAdm.addItem(
                QSelvansListItem(codeadm,
                                 adm,
                                 feature.geometry().boundingBox())
            )

    def zoomToSelectedAdministration(self, item):
        """
        Set map canvas extent to selected administration extent
        """
        self.canvas.setExtent(item.extentRectangle)
        self.canvas.refresh()

    def zoomToSelectedDivision(self, item):
        """
        Set map canvas extent to selected administration extent
        """
        self.canvas.setExtent(item.extentRectangle)
        self.canvas.refresh()

    def selectDivision(self, item):
        """
        Select Division belonging to clicked Administration
        """
        self.dlg.listDiv.clear()
        whereClause = " adm = '" + item.text() + "'"
        divLayer = self.pgdb.getLayer("parcellaire",
                                      "divisions",
                                      "geom",
                                      whereClause,
                                      "listDiv",
                                      "idobj")
        features = divLayer.getFeatures()
        i = 0
        nameList = []
        for feature in features:
            i += 1
            attrs = feature.attributes()
            idx = divLayer.fields().indexFromName("nom")
            nomdiv = attrs[idx]
            idx = divLayer.fields().indexFromName("adm")
            nomadm = attrs[idx]
            idx = divLayer.fields().indexFromName("idne")
            idne = attrs[idx]
            self.dlg.listDiv.addItem(
                QSelvansListItem(idne, str(nomadm) + str(nomdiv),
                                 feature.geometry().boundingBox())
             )


"""
    Subclass the QListWidgetItem to custom needs
"""


class QSelvansListItem(QListWidgetItem):

    def __init__(self, id, text, extentRectangle):
        self.itemId = id
        self.extentRectangle = extentRectangle
        super(QSelvansListItem, self).__init__()
        if text is not None:
            self.setText(text)

    def setId(self, id):
        self.itemId = id
