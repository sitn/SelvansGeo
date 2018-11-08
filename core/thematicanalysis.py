# -*- coding: utf-8 -*-

from builtins import str
from builtins import object
from uuid import uuid4
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtWidgets import QFileDialog, QProgressBar
from qgis.core import QgsVectorLayer, QgsField, QgsFeature, QgsProject
from qgis.core import QgsCoordinateReferenceSystem, QgsMapLayerStyle
from qgis.core import QgsGeometry, QgsVectorFileWriter
from qgis.gui import QgsMessageBar

qversion = 3
try:
    from qgis.PyQt.QtCore import qVersion
    from qgis.core import QgsVectorLayerJoinInfo

except ImportError:
    qversion = 2
    from qgis.core import QgsVectorJoinInfo as QgsVectorLayerJoinInfo
    from qgis.core import QgsMapLayerRegistry


class ThematicAnalysis(object):

    def __init__(self, iface, dlg, pgdb, qtmsdb):
        """
        The ThematicAnalysis constructor
        """
        self.projectInstance = QgsProject.instance()  # SET NAME CORRECTLY!!!
        self.dlg = dlg
        self.pgdb = pgdb
        self.qstr = ""
        self.qtmsdb = qtmsdb
        self.iface = iface
        self.messageBar = self.iface.messageBar()

    def createAnalysis(self):

        newTableName = self.dlg.cmbAnalysis.currentText()

        analysisLayerList = self.projectInstance.mapLayersByName(newTableName)
        if len(analysisLayerList) == 0:
            analysisLayer = QgsVectorLayer("Polygon?crs=EPSG:2056",
                                           newTableName,
                                           "memory")
            analysisDp = analysisLayer.dataProvider()
            analysisCreateNewLayer = True
        elif len(analysisLayerList) == 1:
            analysisLayer = analysisLayerList[0]
            analysisDp = analysisLayer.dataProvider()
            analysisCreateNewLayer = False

        # Delete all existing features in layer if applicable
        iter = analysisLayer.getFeatures()
        featuresToDelete = []
        for feature in iter:
            featuresToDelete.append(feature.id())
        analysisDp.deleteFeatures(featuresToDelete)

        # Check if one analysis is selected
        selectedIndex = self.dlg.cmbAnalysis.currentIndex()
        if selectedIndex == 0:
            self.messageBar.pushWarning("Erreur ",
                                        str(u"Sélectionnez une analyse!"))
            return

        # Get the analysis parameters
        params = self.getAnalysisFromDb()
        self.qstr = params["querystring"]
        if self.qstr is None or self.qstr == "":
            self.messageBar.pushWarning("Erreur",
                                        str(u"Requête mal définie") + self.qstr)
            return

        # Validate user inputs
        if (self.dlg.lnYearStart.text() == ""
            and params["date_filtering"]
                and not self.dlg.chkLastSurvey.isChecked()):

            self.messageBar.pushCritical("Erreur",
                                         "Vous devez saisir une date "
                                         + newTableName)
            return

        if ((self.dlg.lnYearStart.text() == ""
             or self.dlg.lnYearEnd.text() == "")
                and params["date_filtering"]
                and params["timerange_filtering"]):

            self.messageBar.pushCritical("Erreur",
                                         "Vous devez  saisir 2 dates"
                                         + newTableName)
            return

        # Adapt connection string if applicable - method could be cleaner...
        if (params["date_filtering"]
            and not self.dlg.chkLastSurvey.isChecked()
                and not params["timerange_filtering"]):

            self.qstr = self.qstr.replace('--EDITTIMESELECT',
                                          ' ,' + self.dlg.lnYearStart.text() +
                                          ' annee ')
            self.qstr = self.qstr.replace('--EDITTIMESTRING',
                                          ' AND ' + params["datefield"] + ' = '
                                          + self.dlg.lnYearStart.text())

        if (params["date_filtering"]
            and self.dlg.chkLastSurvey.isChecked()
                and not params["timerange_filtering"]):

            self.qstr = self.qstr.replace('--EDITTIMESELECT',
                                          ' , max(' + params["datefield"]
                                          + ') annee ')

        if (params["date_filtering"]
                and params["timerange_filtering"]):
            self.qstr = self.qstr.replace('--STARTYEAR',
                                          self.dlg.lnYearStart.text())
            self.qstr = self.qstr.replace('--ENDYEAR',
                                          self.dlg.lnYearEnd.text())

        coupeFilter = self.dlg.lnCoupeType.text()
        self.editCoupeFilter(coupeFilter, params["coupetype_filtering"])

        admFilter = self.dlg.txtAdmShortName.text()
        self.editAdmFilter(admFilter)

        # Advanced users and developers can see and edit the Query string
        if self.dlg.btAdvancedUserMode.isChecked():
            self.qstr = self.dlg.txtMssqlQuery.toPlainText()
        # Get the geometric layer from PostGIS
        pgLayer = self.pgdb.getLayer(params["join_target_schema"],
                                     params["join_target_table"],
                                     "geom",
                                     "",
                                     params["join_target_table"],
                                     "fake_id")

        if not pgLayer:
            self.messageBar.pushCritical("Erreur au chargement de la couche",
                                         params["join_target_schema"] + '.' +
                                         params["join_target_table"])
            return

        # Execute the query and parse the results
        query = self.qtmsdb.exec_(self.qstr)
        # TODO: Check query validity
        query.setForwardOnly(True)

        # Create memory layer and add it to LegendInterface
        joinTableName = "SELVANS"
        selvansTable = QgsVectorLayer("Point?crs=EPSG:2056",
                                      joinTableName,
                                      "memory")

        selvansTableProvider = selvansTable.dataProvider()

        # Add fields with type given as defined in table main.analysis
        fieldList = params["field_of_interest"].split(",")
        joinedFieldsNames = []
        if params["field_of_interest_type"] == "number":
            for fieldname in fieldList:
                selvansTableProvider.addAttributes([QgsField(
                    params["join_source_fkfield"], QVariant.Int)])
                selvansTableProvider.addAttributes([QgsField(
                    fieldname, QVariant.Double)])
                joinedFieldsNames.append(joinTableName + '_' + fieldname)
        else:
            for fieldname in fieldList:
                selvansTableProvider.addAttributes([QgsField(
                    params["join_source_fkfield"], QVariant.Int)])
                selvansTableProvider.addAttributes([QgsField(
                    fieldname, QVariant.String)])
                joinedFieldsNames.append(joinTableName + '_' + fieldname)

        # Some more field are required for tables related to surveys
        if params["date_filtering"]:
            selvansTableProvider.addAttributes([QgsField(
                'ANNEE_VALEUR', QVariant.Int)])
            joinedFieldsNames.append(joinTableName + '_' + 'ANNEE_VALEUR')
            fieldList.append('ANNEE_VALEUR')
            selvansTableProvider.addAttributes([
                QgsField('DIV_SERIE', QVariant.Int)])
            joinedFieldsNames.append(joinTableName + '_DIV_SERIE')
            fieldList.append('DIV_SERIE')

        # Create progress bar
        progress = self.createProgressbar(query.numRowsAffected())

        # Parse the query result and add the features to memory layer
        self.fillSelvansTable(query,
                              selvansTableProvider,
                              progress, fieldList,
                              params["join_source_fkfield"])
        selvansTable.updateFields()
        self.projectInstance.addMapLayer(selvansTable, False)
        self.projectInstance.addMapLayer(pgLayer, False)
        self.messageBar.clearWidgets()

        # Join the memory layer to a geographic PG layer
        # NOTE: layers MUST be added to the project for join to work in pyQGIS
        targetlayer = self.joinLayer(pgLayer,
                                     params["join_target_pkfield"],
                                     selvansTable,
                                     params["join_source_fkfield"])

        # Get the fields names of the PG layer
        fields = targetlayer.fields()
        fieldslist = []
        for field in fields:
            fieldslist.append(field)

        # Copy the features to the result layer
        analysisDp.deleteAttributes(analysisDp.attributeIndexes())
        analysisLayer.updateFields()
        analysisDp.addAttributes(fieldslist)
        analysisLayer.updateFields()

        outFeat = QgsFeature()
        iter = targetlayer.getFeatures()
        for inFeat in iter:
            if inFeat.geometry():
                outFeat.setGeometry(inFeat.geometry())
                outFeat.setAttributes(inFeat.attributes())
                analysisDp.addFeatures([outFeat])

        analysisLayer.updateFields()
        # QgsProject.instance().addMapLayer(analysisLayer)

        if self.dlg.chkSaveAnalysisResult.isChecked():
            self.saveAnalysisToDisk(analysisLayer)

        if analysisCreateNewLayer:
            self.messageBar.pushCritical("Avertissement",
                                         str(u"La couche est manquante - " +
                                             u"mettre à jour l'impression..."))

            root = QgsProject.instance().layerTreeRoot()
            sgeoGroup = root.findGroup('Analyses SELVANS')
            if sgeoGroup:
                sgeoGroup.addLayer(analysisLayer)
            else:
                QgsProject.instance().addMapLayer(analysisLayer)

        self.activateLastAnalysis(analysisLayer)
        if qversion == 3:
            self.expandGroup("Analyses SELVANS", True)
        else:
            print("handle that too")
        # 24.11.2016: deactivated for now
        self.setStyleFromDb(params, pgLayer, analysisLayer)
        analysisLayer.triggerRepaint()

        # Zoom to selected administration(s)
        self.zoomToSelectedAdministration(admFilter)

        # remove temporary map layers from project
        # Backward compatibility QGIS3=>2
        if qversion == 3:
            self.projectInstance.removeMapLayer(selvansTable)
            self.projectInstance.removeMapLayer(pgLayer)
        else:
            print("handle that")

    def zoomToSelectedAdministration(self, admFilter):
        if admFilter != '':
            admFilter = ' adm = \'' + admFilter
            adminSql = admFilter.replace(',', '\' OR adm = \'')
            adminSql += '\''
            admLayer = self.pgdb.getLayer("parcellaire",
                                          "administrations",
                                          "geom",
                                          adminSql,
                                          "adminSubset",
                                          "idobj")

            if admLayer.featureCount() > 0:
                admExtent = admLayer.extent()
                self.iface.mapCanvas().setExtent(admExtent)
                self.iface.mapCanvas().refresh()
            return

        else:
            return

    def setStyleFromDb(self, params, pgLayer, analysisLayer):
        # Apply the style stored in public.layer_styles to the result layer

        if qversion != 3:
            self.messageBar.pushWarning("Avertissement",
                                        str(u"Le style par défaut n'est pas " +
                                            u"chargé dans QGIS 2.18"))
            return

        p = params["default_style"]
        if p is not None and str(p) != 'NULL':
            qmlstyle = pgLayer.getStyleFromDatabase(params["default_style"])
            qDoc = QDomDocument(params["default_style"])
            qDoc.setContent(qmlstyle[0])
            if qversion == 3:
                styleOk = analysisLayer.importNamedStyle(qDoc)
            else:
                styleOk = analysisLayer.loadNamedStyle(qDoc)

            if styleOk[0]:

                self.messageBar.pushInfo("Info",
                                         str(u"Style par défaut chargé " +
                                             "depuis la base" +
                                             "de données"))
            else:
                self.messageBar.pushWarning("Erreur",
                                            str(u"Style pas défaut non " +
                                                "valide"))

        else:
            self.messageBar.pushWarning("Erreur",
                                        str(u"Style non défini dans la " +
                                            "table main.analysis"))

    def editCoupeFilter(self, coupeFilter, coupetypefiltering):

        if coupetypefiltering and coupeFilter != '':
            subString = ''
            if len(coupeFilter.split(';')) > 1:
                i = 0
                for val in coupeFilter.split(';'):
                    if i == 0:
                        subString += ' AND (COU_COUMOT_ID = \'' + val + '\''
                        i += 1
                    else:
                        subString += ' OR COU_COUMOT_ID = \'' + val + '\''
                subString += ' )'
            else:
                subString = ' AND COU_COUMOT_ID = \'' + coupeFilter + '\''

            self.qstr = self.qstr.replace('--EDITCOUPETYPE', subString)

    def editAdmFilter(self, admFilter):
        if admFilter != '':
            subString = ''
            if len(admFilter.split(';')) > 1:
                i = 0
                for val in admFilter.split(';'):
                    if i == 0:
                        subString += ' AND (Administrations.'
                        subString += 'ADM_NOM_COURT = \'' + val + '\''
                        i += 1
                    else:
                        subString += ' OR Administrations.'
                        subString += 'ADM_NOM_COURT = \'' + val + '\''
                subString += ' )'
            else:
                subString = ' AND Administrations.'
                subString += 'ADM_NOM_COURT = \'' + admFilter + '\''

            self.qstr = self.qstr.replace('--EDITADMCODE', subString)

    def fillSelvansTable(self,
                         query,
                         selvansTableProvider,
                         progress,
                         fieldList,
                         fkField):
        """
        Read the results of the query on Selvans SQL Server Database
        """
        k = 0
        resultFeatures = []
        while query.next():
            k += 1
            progress.setValue(k)
            record = query.record()
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry())
            fieldValueList = [record.field(fkField).value()]
            for fieldName in fieldList:
                fieldValueList.append(record.field(fieldName).value())
            feat.setAttributes(fieldValueList)
            resultFeatures.append(feat)
        selvansTableProvider.addFeatures(resultFeatures)

        if k == 0:
            self.messageBar.pushWarning("Attention",
                                        str(u"Résultat vide! : "))
            return

    def createProgressbar(self, loopnumber):
        """
        Create a progress bar when iterating over features
        """
        progressMessageBar = self.messageBar.createMessage(
            str(u"Chargement des données..."))
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(loopnumber)
        progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        self.messageBar.pushWidget(progressMessageBar)

        return progress

    def expandGroup(self, groupname, expanded):
        """
        Expand a layer group given by its name
        """
        root = QgsProject.instance().layerTreeRoot()
        groupToExpand = root.findGroup(groupname)
        if groupToExpand:
            groupToExpand.setExpanded(expanded)

    def activateLastAnalysis(self, analysisLayer):
        """
        Activates only the last analysis layer in legend interface
        """
        # Backward compatibility QGIS 3=>2
        if qversion == 3:
            root = QgsProject.instance().layerTreeRoot()
            analysisLayerNode = root.findLayer(analysisLayer)

            sgeoGroup = root.findGroup('Analyses SELVANS')
            if sgeoGroup:
                sgeoGroup.setItemVisibilityCheckedRecursive(False)

            if analysisLayerNode:
                analysisLayerNode.setItemVisibilityCheckedParentRecursive(
                    False)
                analysisLayerNode.setItemVisibilityCheckedParentRecursive(True)
        else:
            lReg = QgsMapLayerRegistry.instance()
            legendInterface = self.iface.legendInterface()
            for i in range(self.dlg.cmbAnalysis.count()):
                layerList = lReg.mapLayersByName(
                    self.dlg.cmbAnalysis.itemText(i))
                if len(layerList) > 0:
                    legendInterface.setLayerVisible(layerList[0], False)

            legendInterface.setLayerVisible(analysisLayer, True)

    def saveAnalysisToDisk(self, layer):
        """
        Save the resulting layer to disk in ESRI shapefile format
        """

        fileDestination = self.dlg.txtAnalysisName.text()
        crs = QgsCoordinateReferenceSystem("EPSG:2056")
        error = QgsVectorFileWriter.writeAsVectorFormat(
            layer, fileDestination, "utf8", crs, "ESRI Shapefile")
        if error == QgsVectorFileWriter.NoError:
            self.messageBar.pushInfo("Enregistrement réussi",
                                     fileDestination)
        else:
            self.messageBar.pushCritical("Échec de l'enregistrement",
                                         fileDestination)

    def openFileDialog(self):
        """
            Open a dialog allowing the user to choose a destination folder/file
        """

        if self.dlg.chkSaveAnalysisResult.isChecked():
            filename = QFileDialog.getSaveFileName(None,
                                                   'Enregistrer le fichier')
            self.dlg.txtAnalysisName.show()
            # Backward compatibility QGIS3=>2
            if qversion == 3:
                self.dlg.txtAnalysisName.setText(filename[0] + ".shp")
            else:
                self.dlg.txtAnalysisName.setText(filename + ".shp")
        else:
            self.dlg.txtAnalysisName.hide()

    def checkLastSurvey(self):
        """
            Enable date field if last survey checkbox is unchecked
        """
        if not self.dlg.chkLastSurvey.isChecked():
            self.dlg.lnYearStart.setEnabled(True)
            self.dlg.lblDateStart.setEnabled(True)
        else:
            self.dlg.lnYearStart.setEnabled(False)
            self.dlg.lblDateStart.setEnabled(False)

    def joinLayer(self, targetlayer, pkfield, sourcelayer, fkfield):
        """
        Join the results of the SQL Server query to the pg layer
        """

        joinInfo = QgsVectorLayerJoinInfo()
        # Backward compatbility QGIS3=>2
        if qversion == 3:
            joinInfo.setTargetFieldName(pkfield)
            joinInfo.setJoinLayer(sourcelayer)
            joinInfo.setJoinFieldName(fkfield)
            joinInfo.setUsingMemoryCache(True)
        else:  # QGIS 2
            joinInfo.targetFieldName = pkfield
            joinInfo.joinLayerId = sourcelayer.id()
            joinInfo.joinFieldName = fkfield
            joinInfo.memoryCache = True
        targetlayer.addJoin(joinInfo)
        targetlayer.updateFields()
        return targetlayer

    def getQueryStringFromDb(self):
        """
            Get the query string from db
        """

        selectedIndex = self.dlg.cmbAnalysis.currentIndex()

        if selectedIndex > 0:
            selectedAnalysis = self.dlg.cmbAnalysis.itemData(selectedIndex)
            queryString = "select * from selvansgeo.analysis where id = "
            queryString += selectedAnalysis
            whereClause = " id = " + selectedAnalysis
            pgLayer = self.pgdb.getLayer("selvansgeo",
                                         "analysis",
                                         None,
                                         whereClause,
                                         "Analysis config",
                                         "fake_id")
            iter = pgLayer.getFeatures()
            for feature in iter:
                attrs = feature.attributes()
                idx = pgLayer.fields().indexFromName("querystring")
                querystring = attrs[idx]
                idx = pgLayer.fields().indexFromName("date_filtering")
                datefiltering = self.toBool(attrs[idx])
                idx = pgLayer.fields().indexFromName("timerange_filtering")
                timerangefiltering = self.toBool(attrs[idx])
                idx = pgLayer.fields().indexFromName("coupetype_filtering")
                coupetypefiltering = self.toBool(attrs[idx])

            if querystring and querystring != "":
                self.dlg.txtMssqlQuery.setPlainText(querystring)
                self.messageBar.pushInfo("Connexion PG",
                                         str(u"Définition " +
                                             u"récupérée avec succès"))
                self.setUpAnalysisGui(datefiltering,
                                      timerangefiltering,
                                      coupetypefiltering)
            else:
                self.dlg.txtMssqlQuery.setPlainText("")
                self.messageBar.pushCritical("Erreur",
                                             str(u"La requête n'est pas " +
                                                 u" définie dans la base"))
        else:
            self.dlg.txtMssqlQuery.setPlainText("")

    # Backward compatbility QGIS3=>2 weird bool type issue handling
    def toBool(self, var):

        if type(var) == bool:
            return var

        if var == 'f':
            return False
        else:
            return True

    def setUpAnalysisGui(self,
                         datefiltering,
                         timerangefiltering,
                         coupetypefiltering):
        """
        Show/Hide the year input dates
        """
        if datefiltering:
            self.dlg.lnYearStart.show()
            self.dlg.lblDateStart.show()
            self.dlg.chkLastSurvey.show()
            if timerangefiltering:
                self.dlg.lblDateStart.setText(str('Début'))
                self.dlg.lnYearEnd.show()
                self.dlg.lblDateEnd.show()
                self.dlg.chkLastSurvey.hide()
                self.dlg.lnYearStart.setEnabled(True)
                self.dlg.lblDateStart.setEnabled(True)
            else:
                self.dlg.lblDateStart.setText(str('Année'))
                self.dlg.lnYearEnd.hide()
                self.dlg.lblDateEnd.hide()
                self.dlg.lblCoupeType.hide()
                self.dlg.lnCoupeType.hide()
                if self.dlg.chkLastSurvey.isChecked():
                    self.dlg.lnYearStart.setEnabled(False)
                    self.dlg.lblDateStart.setEnabled(False)

        else:
            self.dlg.lnYearStart.hide()
            self.dlg.lblDateStart.hide()
            self.dlg.chkLastSurvey.hide()
            self.dlg.lnYearEnd.hide()
            self.dlg.lblDateEnd.hide()

        if coupetypefiltering:
            self.dlg.lblCoupeType.show()
            self.dlg.lnCoupeType.show()
        else:
            self.dlg.lblCoupeType.hide()
            self.dlg.lnCoupeType.hide()

    def getAnalysisFromDb(self):
        """
            Load analysis parameters from selvansgeo.analysis table
        """

        selectedIndex = self.dlg.cmbAnalysis.currentIndex()
        if selectedIndex > 0:
            selectedAnalysis = self.dlg.cmbAnalysis.itemData(selectedIndex)
            queryString = "select * from selvansgeo.analysis where id = "
            queryString += selectedAnalysis
            whereClause = " id = " + selectedAnalysis
            pgLayer = self.pgdb.getLayer("selvansgeo",
                                         "analysis",
                                         None,
                                         whereClause,
                                         "Analysis config",
                                         "fake_id")

            iter = pgLayer.getFeatures()
            for feature in iter:
                attrs = feature.attributes()
                idx = pgLayer.fields().indexFromName("id")
                analysis_id = attrs[idx]
                idx = pgLayer.fields().indexFromName("join_target_pkfield")
                join_target_pkfield = attrs[idx]
                idx = pgLayer.fields().indexFromName("join_target_table")
                join_target_table = attrs[idx]
                idx = pgLayer.fields().indexFromName("join_target_schema")
                join_target_schema = attrs[idx]
                idx = pgLayer.fields().indexFromName("join_source_fkfield")
                join_source_fkfield = attrs[idx]
                idx = pgLayer.fields().indexFromName("field_of_interest")
                field_of_interest = attrs[idx]
                idx = pgLayer.fields().indexFromName("field_of_interest_type")
                field_of_interest_type = attrs[idx]
                idx = pgLayer.fields().indexFromName("querystring")
                querystring = attrs[idx]
                idx = pgLayer.fields().indexFromName("id")
                id = attrs[idx]
                idx = pgLayer.fields().indexFromName("default_symbology")
                default_style = attrs[idx]
                idx = pgLayer.fields().indexFromName("date_filtering")
                date_filtering = attrs[idx]
                idx = pgLayer.fields().indexFromName("pie_chart")
                pie_chart = attrs[idx]
                idx = pgLayer.fields().indexFromName("pie_chart_colors")
                pie_chart_colors = attrs[idx]
                idx = pgLayer.fields().indexFromName("datefield")
                datefield = attrs[idx]
                idx = pgLayer.fields().indexFromName("timerange_filtering")
                timerangefiltering = attrs[idx]
                idx = pgLayer.fields().indexFromName("coupetype_filtering")
                coupetypefiltering = attrs[idx]

            return {"analysis_id": analysis_id,
                    "join_target_pkfield": join_target_pkfield,
                    "join_target_table": join_target_table,
                    "join_target_table": join_target_table,
                    "join_target_schema": join_target_schema,
                    "join_source_fkfield": join_source_fkfield,
                    "field_of_interest": field_of_interest,
                    "field_of_interest_type": field_of_interest_type,
                    "querystring": querystring,
                    "default_style": default_style,
                    "date_filtering": self.toBool(date_filtering),
                    "id": id,
                    "pie_chart": pie_chart,
                    "pie_chart_colors": pie_chart_colors,
                    "datefield": datefield,
                    "timerange_filtering": self.toBool(timerangefiltering),
                    "coupetype_filtering": self.toBool(coupetypefiltering)}
