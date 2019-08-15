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

        query = "(select nom, numero, idobj, geom from " + \
                " parcellaire.arrondissements order by nom asc)"
        arrLayer = self.pgdb.getLayer("", query, "geom", "",
                                      "listArr", "idobj")

        if arrLayer:
            features = arrLayer.getFeatures()
        else:
            return

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

        query = "(select adm, idobj, geom from parcellaire.administrations" + \
                " where " + whereClause + " order by adm asc)"
        admLayer = self.pgdb.getLayer("", query, "geom", "",
                                      "listAdm", "idobj")

        if admLayer:
            features = admLayer.getFeatures()
        else:
            return
        i = 0

        nameList = []
        for feature in features:
            i += 1
            attrs = feature.attributes()
            idx = admLayer.fields().indexFromName("adm")
            adm = attrs[idx]
            self.dlg.listAdm.addItem(
                QSelvansListItem(adm,
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

        query = "(select nom, adm, idobj, geom from parcellaire.divisions " +  \
                "where " + whereClause + " order by nom asc)"

        divLayer = self.pgdb.getLayer("", query, "geom", "", "listDiv", "idobj")

        if divLayer:
            features = divLayer.getFeatures()
        else:
            return

        i = 0
        nameList = []
        for feature in features:
            i += 1
            attrs = feature.attributes()
            idx = divLayer.fields().indexFromName("nom")
            nomdiv = attrs[idx]
            idx = divLayer.fields().indexFromName("adm")
            nomadm = attrs[idx]
            idx = divLayer.fields().indexFromName("idobj")
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
