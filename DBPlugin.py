# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import QMenu, QToolBar, QAction, QMessageBox
from PyQt5.QtGui import QIcon
from qgis.core import QgsProject, QgsMessageLog
from .DB_Werkzeug import DB_Werkzeug

class DBPlugin:
    """Main class for the plugin"""

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

        # Get plugin path
        self.pluginPath = os.path.dirname(__file__)

    def initGui(self):
        """Creates the menu entries and toolbar icons inside the QGIS GUI when plugin is loaded."""

        # Add main menu if it doesnt exist

        self.mainMenu = QMenu(self.iface.mainWindow())
        self.mainMenu.setObjectName('Datenbankverbindung')
        self.mainMenu.setTitle('&Datenbankverbindung')
        self.menuBar = self.iface.mainWindow().menuBar()
        self.menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.mainMenu)

        # Add toolbar
        self.toolbar = self.iface.addToolBar('DB Werkzeug')
        self.toolbar.setObjectName('DB Werkzeug')

        # Add action
        self.action = QAction('DB Werkzeug', self.iface.mainWindow())
        self.action.setIcon(QIcon(os.path.join(self.pluginPath, 'icons', 'dbicon.png')))
        self.action.setObjectName('DB Werkzeug')
        self.mainMenu.addAction(self.action) #self.menuTool.addAction(self.action)
        self.toolbar.addAction(self.action)

        self.action.triggered.connect(self.start)

    def unload(self):
        """Removes the plugin menu and toolbar from QGIS GUI when plugin is deactivated."""

        # Remove toolbar
        self.toolbar.deleteLater()

        # Remove main menu
        self.mainMenu.deleteLater()

    def start(self):
        self.dlg = DB_Werkzeug(self.iface)
        self.dlg.exec()
