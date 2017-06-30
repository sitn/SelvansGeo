# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt, QVariant
from PyQt4.QtGui import QFileDialog, QProgressBar
from qgis.core import QgsVectorLayer, QgsField, QgsFeature, QgsMapLayerRegistry
from qgis.core import QgsGeometry, QgsVectorFileWriter, QgsVectorJoinInfo
from qgis.gui import QgsMessageBar


class ThematicAnalysis:

    def __init__(self, iface, dlg, legendInterface, layerRegistry, pgdb, msdb):
        """
        The ThematicAnalysis constructor
        """
        self.legendInterface = legendInterface
        self.lReg = layerRegistry
        self.dlg = dlg
        self.pgdb = pgdb
        self.msdb = msdb
        self.qstr = ""
        self.qtmsdb = None
        self.iface = iface
        self.messageBar = self.iface.messageBar()

    def createAnalysis(self):

        newTableName = self.dlg.cmbAnalysis.currentText()

        analysisLayerList = self.lReg .mapLayersByName(newTableName)
        if len(analysisLayerList) == 0:
            analysisLayer = QgsVectorLayer("Polygon?crs=EPSG:2056",
                                           newTableName,
                                           "memory")
            analysisLp = analysisLayer.dataProvider()
            analysisCreateNewLayer = True
        elif len(analysisLayerList) == 1:
            analysisLayer = analysisLayerList[0]
            analysisLp = analysisLayer.dataProvider()
            analysisCreateNewLayer = False

        # Delete all existing features in layer if applicable
        iter = analysisLayer.getFeatures()
        featureToDelete = []
        for feature in iter:
            featureToDelete.append(feature.id())
        analysisLp.deleteFeatures(featureToDelete)

        # Create PyQt connection to MSSQL if not already there
        if not self.qtmsdb:
            self.qtmsdb, isMSOpened = self.msdb.createQtMSDB()
            if isMSOpened:
                self.messageBar.pushMessage("Connexion SQL Server",
                                            unicode("Connexion réussie!",
                                                    "utf-8"),
                                            level=QgsMessageBar.INFO)
            else:
                return

        selectedIndex = self.dlg.cmbAnalysis.currentIndex()

        if selectedIndex == 0:
            self.messageBar.pushMessage("Erreur ",
                                        unicode("Sélectionnez une analyse!",
                                                "utf-8"),
                                        level=QgsMessageBar.WARNING)
            return

        # Get the analysis parameters
        params = self.getAnalysisFromDb()
        self.qstr = params["querystring"]

        if self.qstr is None or self.qstr == "":
            self.messageBar.pushMessage("Erreur",
                                        unicode("Requête mal définie",
                                                "utf-8") + self.qstr,
                                        level=QgsMessageBar.WARNING)
            return

        # Adapt connection string if applicable - method could be cleaner...
        if (self.dlg.lnYearStart.text() == ""
            and params["date_filtering"] == 't'
                and not self.dlg.chkLastSurvey.isChecked()):

            self.messageBar.pushMessage("Erreur",
                                        "Vous devez saisir une date "
                                        + newTableName,
                                        level=QgsMessageBar.CRITICAL)
            return

        if ((self.dlg.lnYearStart.text() == ""
            or self.dlg.lnYearEnd.text() == "")
                and params["date_filtering"] == 't'
                and params["timerange_filtering"] == 't'):

            self.messageBar.pushMessage("Erreur",
                                        "Vous devez  saisir 2 dates"
                                        + newTableName,
                                        level=QgsMessageBar.CRITICAL)
            return

        if (params["date_filtering"] == 't'
            and not self.dlg.chkLastSurvey.isChecked()
                and params["timerange_filtering"] == 'f'):

            self.qstr = self.qstr.replace('--EDITTIMESELECT',
                                          ' ,' + self.dlg.lnYearStart.text() +
                                          ' annee ')
            self.qstr = self.qstr.replace('--EDITTIMESTRING',
                                          ' AND ' + params["datefield"] + ' = '
                                          + self.dlg.lnYearStart.text())

        if (params["date_filtering"] == 't'
            and self.dlg.chkLastSurvey.isChecked()
                and params["timerange_filtering"] == 'f'):

            self.qstr = self.qstr.replace('--EDITTIMESELECT',
                                          ' , max(' + params["datefield"]
                                          + ') annee ')

        if (params["date_filtering"] == 't'
                and params["timerange_filtering"] == 't'):
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
            self.messageBar.pushMessage("Erreur au chargement de la couche",
                                        params["join_target_schema"] + '.' +
                                        params["join_target_table"],
                                        level=QgsMessageBar.CRITICAL)
            return

            # Execute the query and parse the results
        query = self.qtmsdb.exec_(self.qstr)
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
        if params["date_filtering"] == 't':
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
        self.lReg .addMapLayer(selvansTable)
        self.messageBar.clearWidgets()

        # Join the memory layer to a geographic PG layer
        targetlayer = self.joinLayer(pgLayer,
                                     params["join_target_pkfield"],
                                     selvansTable,
                                     params["join_source_fkfield"])

        # Get the fields names of the PG layer
        fields = targetlayer.pendingFields()
        fieldslist = []
        fieldNamesTest = []
        for field in fields:
            fieldslist.append(field)
            fieldNamesTest.append(field.name())

        # Add the features to the result layer
        analysisLp.deleteAttributes(analysisLp.attributeIndexes())
        analysisLp.addAttributes(fieldslist)
        outFeat = QgsFeature()
        iter = targetlayer.getFeatures()

        for inFeat in iter:
            if inFeat.geometry():
                outFeat.setGeometry(inFeat.geometry())
                outFeat.setAttributes(inFeat.attributes())
                analysisLp.addFeatures([outFeat])

        analysisLayer.updateFields()
        QgsMapLayerRegistry.instance().addMapLayer(analysisLayer)

        # # Apply the style store in public.layer_styles to the result layer
        # # 24.11.2016: deactivated for now
        # if params["default_style"] is not None:
        #     qmlstyle = pgLayer.getStyleFromDatabase(params["default_style"],
        #                                             "")
        #     analysisLayer.applyNamedStyle(qmlstyle)
        # else:
        #     self.messageBar.pushMessage("Erreur",
        #                                 unicode("Style non défini dans la "
        #                                         + "table main.analysis",
        #                                         "utf-8"),
        #                                 level=QgsMessageBar.WARNING)

        if self.lReg .mapLayersByName('SELVANS'):
            self.lReg .removeMapLayer(
                self.lReg .mapLayersByName('SELVANS')[0].id()
            )

        if self.dlg.chkSaveAnalysisResult.isChecked():
            self.saveAnalysisToDisk(analysisLayer)

        if analysisCreateNewLayer:
            self.messageBar.pushMessage("Avertissement",
                                        unicode("La couche manquante",
                                                "utf-8"),
                                        level=QgsMessageBar.WARNING)
            self.moveLayerToGroup(analysisLayer, "Analyses SELVANS")

        self.activateLastAnalysis(analysisLayer)
        self.expandGroup(analysisLayer, "Analyses SELVANS", True)

        analysisLayer.triggerRepaint()
        self.legendInterface.refreshLayerSymbology(analysisLayer)

        # Zoom to selected administration(s)
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
            else:
                self.messageBar.pushMessage("Avertissement",
                                            "Administration(s)" + admFilter +
                                            " manquante dans la base PostGIS!",
                                            level=QgsMessageBar.WARNING)

    def editCoupeFilter(self, coupeFilter, coupetypefiltering):

        if coupetypefiltering == 't' and coupeFilter != '':
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
            self.messageBar.pushMessage("Attention",
                                        unicode("Résultat vide! : ", "utf-8"),
                                        level=QgsMessageBar.WARNING)
            return

    def createProgressbar(self, loopnumber):
        """
        Create a progress bar when iterating over features
        """
        progressMessageBar = self.messageBar.createMessage(
            unicode("Chargement des données...", "utf-8"))
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(loopnumber)
        progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        self.messageBar.pushWidget(progressMessageBar, self.messageBar.INFO)

        return progress

    def moveLayerToGroup(self, layer, groupname):
        """
        Move a layer to a group identified by its name
        """
        groups = self.legendInterface.groups()
        if groupname in groups:
            groupIndex = groups.index(groupname)
            self.legendInterface.moveLayer(layer, groupIndex)

    def expandGroup(self, layer, groupname, expanded):
        """
        Expand a layer group given by its name
        """
        groups = self.legendInterface.groups()
        if groupname in groups:
            groupIndex = groups.index(groupname)
            groupIndex = groups.index(groupname)
            self.legendInterface.setGroupExpanded(groupIndex, expanded)

    def activateLastAnalysis(self, analysisLayer):
        """
        Activates only the last analysis layer in legend interface
        """

        for i in range(self.dlg.cmbAnalysis.count()):
            layerList = self.lReg .mapLayersByName(
                self.dlg.cmbAnalysis.itemText(i))
            if len(layerList) > 0:
                self.legendInterface.setLayerVisible(layerList[0], False)

        self.legendInterface.setLayerVisible(analysisLayer, True)

    def saveAnalysisToDisk(self, layer):
        """
        Save the resulting layer to disk in ESRI shapefile format
        """

        fileDestination = self.dlg.txtAnalysisName.text()
        error = QgsVectorFileWriter.writeAsVectorFormat(
            layer, fileDestination, "utf8", None, "ESRI Shapefile")
        if error == QgsVectorFileWriter.NoError:
            self.messageBar.pushMessage("Enregistrement réussi",
                                        fileDestination,
                                        level=QgsMessageBar.INFO)
        else:
            self.messageBar.pushMessage("Échec de l'enregistrement",
                                        fileDestination,
                                        level=QgsMessageBar.CRITICAL)

    def openFileDialog(self):
        """
            Open a dialog allowing the user to choose a destination folder/file
        """

        if self.dlg.chkSaveAnalysisResult.isChecked():
            filename = QFileDialog.getSaveFileName(None,
                                                   'Enregistrer le fichier')
            self.dlg.txtAnalysisName.show()
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

        joinInfo = QgsVectorJoinInfo()
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
                idx = pgLayer.fieldNameIndex("querystring")
                querystring = attrs[idx]
                idx = pgLayer.fieldNameIndex("date_filtering")
                datefiltering = attrs[idx]
                idx = pgLayer.fieldNameIndex("timerange_filtering")
                timerangefiltering = attrs[idx]
                idx = pgLayer.fieldNameIndex("coupetype_filtering")
                coupetypefiltering = attrs[idx]

            if querystring and querystring != "":
                self.dlg.txtMssqlQuery.setPlainText(querystring)
                self.messageBar.pushMessage("Connexion PG",
                                            unicode("Définition " +
                                                    "récupérée avec succès",
                                                    "utf-8"),
                                            level=QgsMessageBar.INFO)
                self.setUpAnalysisGui(datefiltering,
                                      timerangefiltering,
                                      coupetypefiltering)
            else:
                self.dlg.txtMssqlQuery.setPlainText("")
                self.messageBar.pushMessage("Erreur",
                                            unicode("La requête n'est pas " +
                                                    " définie dans la base",
                                                    "utf-8"),
                                            level=QgsMessageBar.CRITICAL)
        else:
            self.dlg.txtMssqlQuery.setPlainText("")

    def setUpAnalysisGui(self,
                         datefiltering,
                         timerangefiltering,
                         coupetypefiltering):
        """
        Show/Hide the year input dates
        """

        if datefiltering == 't':
            self.dlg.lnYearStart.show()
            self.dlg.lblDateStart.show()
            self.dlg.chkLastSurvey.show()
            if timerangefiltering == 't':
                self.dlg.lblDateStart.setText(unicode('Début', "utf-8"))
                self.dlg.lnYearEnd.show()
                self.dlg.lblDateEnd.show()
                self.dlg.chkLastSurvey.hide()
                self.dlg.lnYearStart.setEnabled(True)
                self.dlg.lblDateStart.setEnabled(True)
            else:
                self.dlg.lblDateStart.setText(unicode('Année', "utf-8"))
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

        if coupetypefiltering == 't':
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
                idx = pgLayer.fieldNameIndex("id")
                analysis_id = attrs[idx]
                idx = pgLayer.fieldNameIndex("join_target_pkfield")
                join_target_pkfield = attrs[idx]
                idx = pgLayer.fieldNameIndex("join_target_table")
                join_target_table = attrs[idx]
                idx = pgLayer.fieldNameIndex("join_target_schema")
                join_target_schema = attrs[idx]
                idx = pgLayer.fieldNameIndex("join_source_fkfield")
                join_source_fkfield = attrs[idx]
                idx = pgLayer.fieldNameIndex("field_of_interest")
                field_of_interest = attrs[idx]
                idx = pgLayer.fieldNameIndex("field_of_interest_type")
                field_of_interest_type = attrs[idx]
                idx = pgLayer.fieldNameIndex("querystring")
                querystring = attrs[idx]
                idx = pgLayer.fieldNameIndex("id")
                id = attrs[idx]
                idx = pgLayer.fieldNameIndex("default_symbology")
                default_style = attrs[idx]
                idx = pgLayer.fieldNameIndex("date_filtering")
                date_filtering = attrs[idx]
                idx = pgLayer.fieldNameIndex("pie_chart")
                pie_chart = attrs[idx]
                idx = pgLayer.fieldNameIndex("pie_chart_colors")
                pie_chart_colors = attrs[idx]
                idx = pgLayer.fieldNameIndex("datefield")
                datefield = attrs[idx]
                idx = pgLayer.fieldNameIndex("timerange_filtering")
                timerangefiltering = attrs[idx]
                idx = pgLayer.fieldNameIndex("coupetype_filtering")
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
                    "date_filtering": date_filtering,
                    "id": id,
                    "pie_chart": pie_chart,
                    "pie_chart_colors": pie_chart_colors,
                    "datefield": datefield,
                    "timerange_filtering": timerangefiltering,
                    "coupetype_filtering": coupetypefiltering}
