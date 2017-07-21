# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SelvansGeo
                                 A QGIS plugin for cross-db thematic mapping
                                 and custom editing

                              -------------------
        begin                : 2014-03-10
        Authors              : 2014-2017 by SITN-OM/SFFN-MG-RB
        email                : olivier.monod@ne.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import

from builtins import str
from builtins import object
import os.path
import sys
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QObject

from qgis.PyQt.QtSql import QSqlDatabase
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon, QIntValidator
from qgis.PyQt.QtGui import QPainter
from qgis.PyQt.QtWidgets import QListWidgetItem, QFileDialog, QMessageBox
from qgis.core import QgsProject, QgsCredentials
from qgis.gui import QgsMessageBar
from . import resources
from .selvansgeodialog import SelvansGeoDialog
from .core.thematicanalysis import ThematicAnalysis
from .core.cartotools import CartoTools
from .core.sitndb import SitnDB
from .core.tabularNavigation import tabularNavigation
from .core.desactivateLayer import DesactivateLayerMapTool
import webbrowser
import yaml

# Set up current path, so that we know where to look for modules
currentPath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/tools'))


class SelvansGeo(object):

    def __init__(self, iface):
        """
        Constructor of SelvanGeo. References to the
        """

        self.conf = yaml.load(
            open(os.path.dirname(os.path.abspath(__file__)) +
                 "\\selvansgeo.yaml", 'r')
        )['vars']

        # Get reference to the QGIS interface
        self.iface = iface

        # A reference to our map canvas
        self.canvas = self.iface.mapCanvas()

        # Get reference to legend interface
        self.legendInterface = None #self.iface.legendInterface()

        # Get reference to the legend interface
        self.layerRegistry = QgsProject.instance()

        # Create the GUI Dialog
        self.dlg = SelvansGeoDialog()

        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # Get the QGIS message bar
        self.messageBar = self.iface.messageBar()

        # Initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n',
                                  'selvansgeo_{}.qm'.format(locale))

        # Globals
        self.currentRole = "init"
        self.credentialInstance = QgsCredentials.instance()
        self.readerPwd = self.conf['pg']['password']

        # Project paths
        self.defaultProjectPath = currentPath + "/qgisprj/" + \
            self.conf['default_project']

        s = QSettings()
        self.customProjectPath = s.value("SelvansGeo/customProject",
                                         self.defaultProjectPath)

        if self.customProjectPath == "":
            self.customProjectPath = self.defaultProjectPath

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        """
        Initialize the GUI, connect SIGNALS
        """

        self.action = QAction(
            QIcon(currentPath + "/icon.png"), u"SelvansGeo",
            self.iface.mainWindow())

        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&SelvansGeo", self.action)

        # disable tabs until user is connected to db
        self.switchUiMode(True)
        # self.switchUiMode(False) # ==> switch on production

        # initialize connections to Application Databases - only reading access
        conf = self.conf
        self.pgdb = SitnDB(conf['pg']['dbname'], conf['pg']['host'],
                           conf['pg']['port'], conf['pg']['user'],
                           self.readerPwd, "postgres", self.iface)

        self.dlg.txtPassword.setText(self.readerPwd)

        # Connection to MSSQL
        self.msdb = SitnDB(conf['ms']['dbname'], conf['ms']['host'], "",
                           conf['ms']['user'], conf['ms']['password'],
                           "mssql", self.iface)
        self.qtmsdb, isMSOpened = self.msdb.createQtMSDB()
        # HANDLE MISSING CONNECTION HERE !!!
        # Thematic Analysis tools
        self.thematicanalysis = ThematicAnalysis(self.iface,
                                                 self.dlg,
                                                 self.pgdb,
                                                 self.qtmsdb)

        # SelvansGeo navigation tools
        self.tabularNavigation = tabularNavigation(self.iface,
                                                   self.dlg,
                                                   self.layerRegistry,
                                                   self.pgdb,
                                                   self.canvas)

        # Selvans cartographic tools
        self.cartotools = CartoTools(self.iface, self.dlg)

        self.fillAnalysisCombo()

        # *** Connect signals and slot***

        # Project
        self.dlg.btLoadProject.clicked.connect(self.openSelvansGeoProject)
        self.dlg.btDefineDefaultProject.clicked.connect(self.defineDefaultProject)
        self.dlg.btResetDefaultProject.clicked.connect(self.resetDefaultProject)

        # Connection
        self.dlg.btConnection.clicked.connect(self.connectionsInit)

        # self.switchUiMode(True)# DEBUG MODE. COMMENT IN PRODUCTION

        self.dlg.cmbConnection.currentIndexChanged.connect(self.setConnectionPwdTxt)

        # CartoTools
        self.dlg.btShowNodes.clicked.connect(self.cartotools.showNodes)
        self.dlg.btDesactivateLayer.clicked.connect(self.setDesactivateLayerTool)
        # CALL THIS AT A BETTER PLACE!!!
        #self.iface.mapCanvas().renderComplete.connect(self.fillLayersCombo)

        # Help
        self.dlg.btQgisPrintComposerHelp.clicked.connect(self.openQgisPrintHelp)
        self.dlg.btQgisHelp.clicked.connect(self.openQgisHelp)
        self.dlg.btSelvansGeoHelp.clicked.connect(self.openSelvansGeoHelp)

        # Navigation tools
        self.dlg.listArr.itemClicked.connect(self.tabularNavigation.selectAdministration)
        self.dlg.listAdm.itemClicked.connect(self.tabularNavigation.selectDivision)
        self.dlg.listAdm.itemDoubleClicked.connect(self.tabularNavigation.zoomToSelectedAdministration)
        self.dlg.listDiv.itemDoubleClicked.connect(self.tabularNavigation.zoomToSelectedDivision)

        # Thematic analysis
        self.dlg.btAnalysis.clicked.connect(self.thematicanalysis.createAnalysis)
        self.dlg.btAdvancedUserMode.clicked.connect(self.analysisAdvancedUserMode)
        self.dlg.cmbAnalysis.currentIndexChanged.connect(self.thematicanalysis.getQueryStringFromDb)
        self.dlg.chkSaveAnalysisResult.stateChanged.connect(self.thematicanalysis.openFileDialog)
        self.dlg.chkLastSurvey.stateChanged.connect(self.thematicanalysis.checkLastSurvey)

        self.dlg.lnYearStart.setValidator(QIntValidator())
        self.dlg.lnYearStart.setMaxLength(4)
        self.dlg.lnYearEnd.setValidator(QIntValidator())
        self.dlg.lnYearEnd.setMaxLength(4)
        self.dlg.lnCoupeType.setValidator(QIntValidator())
        self.analysisAdvancedUserMode()
        self.dlg.frameIcon.setStyleSheet("image: url(" + currentPath +
                                         "/icon.png)")

        # Set default visibility of some GUI items
        self.dlg.lnYearStart.hide()
        self.dlg.lblDateStart.hide()
        self.dlg.chkLastSurvey.hide()
        self.dlg.txtAnalysisName.hide()
        self.dlg.lnCoupeType.hide()
        self.dlg.lblCoupeType.hide()
        self.dlg.lnYearEnd.hide()
        self.dlg.lblDateEnd.hide()
        self.dlg.chkSaveAnalysisResult.show()

        # Set label about project paths
        self.dlg.lblCurrentProject.setText(self.customProjectPath)

    # Define custom SelvanGeo Project path in user settings
    def defineDefaultProject(self):
        filename = QFileDialog.getOpenFileName(None, 'Choisir un projet')
        s = QSettings()
        s.setValue("SelvansGeo/customProject", filename[0])
        self.customProjectPath = filename[0]
        # Set label about project path
        self.dlg.lblCurrentProject.setText(self.customProjectPath)

    def resetDefaultProject(self):
        s = QSettings()
        s.setValue("SelvansGeo/customProject", self.defaultProjectPath)
        self.customProjectPath = self.defaultProjectPath
        # Set label about project paths
        self.dlg.lblCurrentProject.setText(self.customProjectPath)

    # reset QLine edit text box containing password
    def setConnectionPwdTxt(self):

        if self.dlg.cmbConnection.currentText() == "Edition":
            # writer credentials are stored in user profile once
            s = QSettings()
            writerCredentials = s.value("SelvansGeo/writerCredentials")
            if writerCredentials:
                self.dlg.txtPassword.setText(writerCredentials)
            else:
                self.dlg.txtPassword.setText("")
        elif self.dlg.cmbConnection.currentText() == "Consultation":
            self.dlg.txtPassword.setText(self.readerPwd)

    # Create connection to SFFN PostGIS DB
    def connectionsInit(self):

        conf = self.conf
        roleSelected = self.dlg.cmbConnection.currentText()

        # Connection string to Postgis db
        connectionInfo = "dbname='" + conf['pg']['dbname'] + "' "
        connectionInfo += "host=" + conf['pg']['host'] + " "
        connectionInfo += "port=" + conf['pg']['port'] + " "
        connectionInfo += "sslmode=disable"

        if roleSelected == 'Edition':
            user = conf["pg"]["editor"]
            pwd = self.dlg.txtPassword.text()
            if pwd == '':
                return
            else:
                s = QSettings()
                s.setValue("SelvansGeo/writerCredentials", pwd)
                # Setup  QGIS credentials dialog
                checkdb = QSqlDatabase.addDatabase("QPSQL")
                checkdb.setHostName(conf['pg']['host'])
                checkdb.setDatabaseName(conf['pg']['dbname'])
                checkdb.setUserName(user)
                checkdb.setPassword(pwd)

                if checkdb.open():
                    self.credentialInstance.put(connectionInfo, user, pwd)
                else:
                    self.messageBar.pushMessage("Erreur",
                                                str("Mauvais mot de passe"),
                                                level=QgsMessageBar.CRITICAL)
                    self.dlg.txtPassword.setText("")
                    return

        elif roleSelected == 'Consultation':
            self.credentialInstance.put(connectionInfo, conf['pg']['user'],
                                        conf['pg']['password'],)

        self.switchUiMode(True)

        if self.currentRole != roleSelected and self.currentRole != "init":
            self.messageBar.pushMessage("Info", str("Vous êtes connecté en"
                                        + "mode ") +
                                        roleSelected, level=QgsMessageBar.INFO)
            self.openSelvansGeoProject()
        else:
            self.messageBar.pushMessage("Info", str("Vous êtes connecté en"
                                        + "mode ") + roleSelected,
                                        level=QgsMessageBar.INFO)
            self.openSelvansGeoProject()
        # store the current role
        self.currentRole = roleSelected

    # Desactivate all UI except connection part
    def switchUiMode(self, mode):

        self.dlg.tabPanel.setTabEnabled(1, mode)
        self.dlg.tabPanel.setTabEnabled(2, mode)
        self.dlg.grpProjects.setEnabled(True)
        self.dlg.btLoadProject.setEnabled(mode)

    def openSelvansGeoProject(self):
        """
        Load the default SelvansGeo QGIS Project
        """
        warningTxt = str("Ceci annulera les modifications non sauvegardée"
                             + "du projet QGIS ouvert actuellement")

        reply = QMessageBox.question(self.dlg, 'Avertissement!', warningTxt,
                                     QMessageBox.Ok | QMessageBox.Cancel,
                                     QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            self.iface.addProject(self.customProjectPath)
            self.iface.actionOpenProject()

    def openQgisPrintHelp(self):
        """
        Link to QGIS print help
        """
        webbrowser.open("http://docs.qgis.org/2.10/fr/docs/user_manual/" +
                        "print_composer/print_composer.html")

    def openQgisHelp(self):
        """
        Link to QGIS main help
        """
        webbrowser.open("http://docs.qgis.org/2.10/fr/docs/user_manual/")

    def openSelvansGeoHelp(self):
        """
        Link to SelvansGeo help
        """
        webbrowser.open("https://sitnintra.ne.ch/projects/qgis_repository/" +
                        "manuel_utilisateur.pdf")

    def setDesactivateLayerTool(self):
        if self.dlg.btDesactivateLayer.isChecked():
            self.desactivateLayerTool = \
                DesactivateLayerMapTool(self.canvas,
                                        self.legendInterface,
                                        self.dlg, self.iface,
                                        self.layerRegistry)

            self.canvas.setMapTool(self.desactivateLayerTool)
        else:
            self.iface.actionPan().trigger()
            self.dlg.btDesactivateLayer.setChecked(False)

    def analysisAdvancedUserMode(self):
        """
        Set up which buttons are shown when advanced user mode is selected
        """
        if self.dlg.btAdvancedUserMode.isChecked():
            self.dlg.txtMssqlQuery.show()
            self.dlg.lblSql.show()
        else:
            self.dlg.txtMssqlQuery.hide()
            self.dlg.lblSql.hide()

    def fillAnalysisCombo(self):
        """
        Fill the QComboBox with the list of analysis available
        """
        self.dlg.cmbAnalysis.clear()
        query = "(select oid, analysis_name, id from " + \
            "selvansgeo.analysis order by id asc)"

        pgLayer = self.pgdb.getLayer("", query, None, "",
                                     "Analysis list", "oid")

        iter = pgLayer.getFeatures()
        for feature in iter:
            attrs = feature.attributes()
            idx = pgLayer.fields().indexFromName("analysis_name")
            analysis_name = attrs[idx]
            idx = pgLayer.fields().indexFromName("id")
            id = attrs[idx]
            self.dlg.cmbAnalysis.addItem(analysis_name, str(id))

    def fillAdminFilterCombo(self):
        """
        Fill the QComboBox with the list of administrations
        """
        self.dlg.cmbAdminFilter.clear()
        query = "(select idobj, adm from" + \
            "parcellaire.administrations order by adm asc)"
        pgLayer = self.pgdb.getLayer("", query, None, "",
                                     "Administration list", "idobj")

        iter = pgLayer.getFeatures()
        for feature in iter:
            attrs = feature.attributes()
            idx = pgLayer.fields().indexFromName("adm")
            administration_name = attrs[idx]
            idx = pgLayer.fields().indexFromName("idobj")
            id = attrs[idx]
            self.dlg.cmbAdminFilter.addItem(administration_name, str(idobj))

    def fillLayersCombo(self):
        """
        Fill the QComboBox with the list of geometric layers
        """
        self.dlg.comboLayers.clear()
        layers = QgsProject.instance().layers()
        for layer in layers:
            # Load only vector layers
            if layer.type() == 0 and layer.name() != 'Noeuds':
                if layer.hasGeometryType():
                    self.dlg.comboLayers.addItem(layer.originalName(), layer)

    def unload(self):
        """
        Remove the plugin menu item and icon
        """
        self.iface.removePluginMenu(u"&SelvansGeo", self.action)
        self.iface.removeToolBarIcon(self.action)

    # run method that performs all the real work
    def run(self):
        """
        show the dialog
        """
        self.dlg.show()
        # CALL THIS, REALLY ???
        #self.fillLayersCombo()
        # Run the dialog event loop
        self.dlg.exec_()
