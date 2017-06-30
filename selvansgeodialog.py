# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from ui_selvansgeo import Ui_SelvansGeo


class SelvansGeoDialog(QtGui.QDialog, Ui_SelvansGeo):

    def __init__(self):
        """
        The SelvansGeo Dialog constructor, set it as allways on top \
        of any QtDialog object
        """
        QtGui.QDialog.__init__(self)
        self.ui = Ui_SelvansGeo()
        self.setupUi(self)
