# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SelvansGeo
                                 A QGIS plugin
 Qgis ToolBox for forest manager
                             -------------------
        begin                : 2014-03-10
        copyright            : (C) 2014 by SITN/SFFN
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
 This script initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    # load SelvansGeo class from file SelvansGeo
    from selvansgeo import SelvansGeo
    return SelvansGeo(iface)
