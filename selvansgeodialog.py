# -*- coding: utf-8 -*-

from qgis.PyQt.QtWidgets import QDialog
# Backward compatibility QGIS 3=>2
try:
    from .ui_selvansgeo import Ui_SelvansGeo
except ImportError:
    from .ui_selvansgeo_qgis2 import Ui_SelvansGeo


class SelvansGeoDialog(QDialog, Ui_SelvansGeo):

    def __init__(self):
        """
        The SelvansGeo Dialog constructor, set it as allways on top \
        of any QtDialog object
        """
        QDialog.__init__(self)
        self.ui = Ui_SelvansGeo()
        self.setupUi(self)
