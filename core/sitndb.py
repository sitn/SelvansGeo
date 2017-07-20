# -*- coding: utf-8 -*-

from builtins import object
from qgis.PyQt.QtSql import QSqlDatabase
from qgis.core import QgsDataSourceUri, QgsVectorLayer
from qgis.gui import QgsMessageBar


class SitnDB(object):
    def __init__(self, dbname, host, port, user, password, providerkey, iface):
        """
            Defines the db connexion parameters and the qgis provider key
        """

        self.uri = QgsDataSourceUri()
        self.uri.setConnection(host, port, dbname, user, password)
        self.providerkey = providerkey
        self.errorMessage = ''
        self.messageBar = iface.messageBar()

    def getLayer(self,
                 shema,
                 table,
                 geomfieldname,
                 whereclause,
                 layername,
                 uniqueidfield):
        """
            Returns a layer or a table. If no geometry is available,
            geomfieldname must be set to None.
        """

        self.uri.setDataSource(shema,
                               table,
                               geomfieldname,
                               whereclause,
                               uniqueidfield)

        layer = QgsVectorLayer(self.uri.uri(), layername, self.providerkey)

        if not layer.isValid():
            return None
        else:
            return layer

    def createQtMSDB(self):
        """
            Returns a db Connection to a MSSQL (SQL Server database) using
            QtSql. This is requiered in order to create views with SQL Server
        """

        db = QSqlDatabase.addDatabase("QODBC")

        if db.isValid():
            db.setDatabaseName("DRIVER={SQL Server};SERVER=" + self.uri.host()
                               + ";DATABASE=" + self.uri.database())
            db.setUserName(self.uri.username())
            db.setPassword(self.uri.password())

            if db.open():
                return db, True

            else:
                self.messageBar.pushMessage("Connection SQl Server",
                                            db.lastError().text(),
                                            level=QgsMessageBar.CRITICAL)
                db.close()
                db.removeDatabase(db.databaseName())
                db = None
                return db, False
        else:
            self.messageBar.pushMessage("Connection SQL Server",
                                        'QODBC db is NOT valid',
                                        level=QgsMessageBar.CRITICAL)
