# -*- coding: utf-8 -*-

# Bibliotheken laden
import os, time
from PyQt5 import uic, Qt
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from qgis.core import *
import psycopg2
import psycopg2.extras
import json
import sys

#wandelt .ui in .py um
pluginPath = os.path.dirname(__file__)
WIDGET, BASE = uic.loadUiType(os.path.join(pluginPath, 'ui', 'maske.ui'))


###################################################################################################
# Reiter
# Fenster DB_Tool, erste Verbindung zu DB anlegen
class DB_Werkzeug(BASE, WIDGET):

    def __init__(self, iface, parent=None):
        super().__init__(parent)

        self.iface = iface
        self.setupUi(self)

        self.cancel.clicked.connect(self.closePlugin)
        self.ok.clicked.connect(self.connected)
        self.btnAktualisieren.clicked.connect(self.listeFuellen)
        self.listeFuellen()
        self.btnDBloeschen.clicked.connect(self.dbLoeschen)
        self.listWidget.setSortingEnabled(True)
        self.listWidget.doubleClicked.connect(self.dsTabelle)
        self.btn_Tab_in_ListWidget.clicked.connect(self.dsTabelle)
        self.listWidget_DS.doubleClicked.connect(self.tabInQGIS)
        
        self.btn_Tab_in_QGIS.clicked.connect(self.tabInQGIS)
        self.btn_Tab_in_QGIS_abfrage.clicked.connect(self.tabInQGisAbfrage)
        
        self.btn_createDB.clicked.connect(self.createDB)
        self.listWidget_DS.setSortingEnabled(True)
        self.btn_testen.clicked.connect(self.testen) 
        
        self.listWidget_DS_2.setSortingEnabled(True)
        self.listWidget_DS_2.doubleClicked.connect(self.tabInQGIS)
        self.listWidget_DS_2.clicked.connect(self.tabellenName)
        self.listWidget_DS_2.clicked.connect(self.spaltenName)
        self.listWidget_spalten.doubleClicked.connect(self.spaltenNameInSqlFenster)
        
        self.listWidget_spalten.clicked.connect(self.werte)
        self.listWidget_werte.doubleClicked.connect(self.werteInSqlFenster)
        
        self.btn_groesser.clicked.connect(self.groesser)
        self.btn_gleich.clicked.connect(self.gleich)
        self.btn_ungleich.clicked.connect(self.ungleich)
        self.btn_kleiner.clicked.connect(self.kleiner)
        self.btn_prozent.clicked.connect(self.prozent)
        self.btn_in.clicked.connect(self.operatorIN)
        self.btn_klammer_auf.clicked.connect(self.klammerAuf)
        self.btn_klammer_zu.clicked.connect(self.klammerZu)
        self.btn_notin.clicked.connect(self.notIN)
        self.btn_like.clicked.connect(self.operatorLike)
        self.btn_and.clicked.connect(self.operatorAnd)
        self.btn_not.clicked.connect(self.operatorNot)
        self.btn_or.clicked.connect(self.operatorOr)
        self.btn_kleiner_oder_gleich.clicked.connect(self.kleinerOderGleich)
        self.btn_groesser_oder_gleich.clicked.connect(self.groesserOderGleich)
        
        self.listWidget_DS_3.setSortingEnabled(True)
        self.listWidget_DS_3.clicked.connect(self.spaltenName2)
        self.listWidget_DS_3.doubleClicked.connect(self.tabellenNameInPostgis)
        self.listWidget_spalten_2.doubleClicked.connect(self.spaltenNameInPostgis)
        self.treeWidget.doubleClicked.connect(self.postGisFunctionName)
        
        self.btn_selektieren.clicked.connect(self.selektierenPostGis)
        self.btn_ausfuehren.clicked.connect(self.ausfuehrenPostGis)
       
        self.label_14.setTextInteractionFlags(Qt.TextSelectableByMouse) 
        self.label_17.setTextInteractionFlags(Qt.TextSelectableByMouse) 
        self.treeWidget.clicked.connect(self.helpPostgis)
        
#Reiter 2
    # füllt die db_liste.json gleich zu Beginn
    def listeFuellen(self):
        # Liste bereinigen
        self.listWidget.clear()
        self.listWidget.setSortingEnabled(True)

        # liest die Datei (DB_Liste)
        self.file_path = os.path.join(pluginPath, 'db_liste.json')
        with open(self.file_path, "r", encoding = 'utf-8') as file:
            self.db_liste = json.load(file)

        for item in self.db_liste["items"]:
            self.listWidget.addItem(item)

###############################################################################################
# Reiter 1

    def closePlugin(self):
        self.close()

    # neue Verbindung zu bestehender DB aufbauen - bestehende DB in db_liste.json aufnehmen
    def connected(self):

        # Connect to an existing database
        try:
            dbname = self.dbname.text()
            user = self.user.text()
            pw = self.pw.text()
            host = self.host.text()
            port = self.port.value()
            self.conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)
            self.cur = self.conn.cursor()
            self.conn.autocommit = True
            print ( self.conn.get_dsn_parameters(),"\n")

            # liest die Datei (DB_Liste)
            with open(self.file_path, "r", encoding = 'utf-8') as file:
                self.db_liste = json.load(file)

            # fuegt DB der DB_Liste hinzu
            self.db_liste["items"].update({dbname:{"user": user,"pw": pw, "host":host,"port":port}})

            # speichert die DB_Liste ab
            with open(self.file_path, "w", encoding = 'utf-8') as file:
                self.db_liste = json.dump(self.db_liste, file, indent=2)

            self.listeFuellen()
            self.label_19.setText("Es hat geklappt :) \nDie Verbindung zur Datenbank "+dbname+" konnte hergestellt werden.")

        except:
            def showMessage(title, mesage):
                QMessageBox.information(None, title, mesage)

            showMessage("Warnung", "Eine Verbindung zu '" + dbname + "' konnte nicht hergestellt werden! \nStellen Sie sicher, dass Sie alle Leerfelder ausgefüllt haben und die entsprechende PostgreSQL-Datenbank existiert. Anderenfalls können Sie eine neue Datenbank erstellen.")

    # neue Datenbank erstellen
    # erstellt eine neuen Datenbank, mit Einstellungen der ausgewählten DB
    def createDB(self):

        def showMessage(title, mesage):
                    QMessageBox.information(None, title, mesage)

        dbname = self.dbname.text()
        user = self.user.text()
        pw = self.pw.text()
        host = self.host.text()
        port = self.port.value()

        if dbname =='':
            showMessage("Warnung", "Der Datenbankname muss ergänzt werden")

        elif user == '':
            showMessage("Warnung", "Der Benutzername muss ergänzt werden")

        elif pw == '':
            showMessage("Warnung", "Das Passwort muss ergänzt werden")

        elif host == '':
            showMessage("Warnung", "Der Host muss ergänzt werden")

        elif port == 0:
            showMessage("Warnung", "Der Port muss ergänzt werden")

        else:
            self.connected = psycopg2.connect(user=user, password=pw, host=host, port=port)
            self.cursor = self.connected.cursor()
            self.connected.autocommit = True
            print ("mit Datenbanken verbunden")

            try:
                create_database = ("""CREATE DATABASE"""+' '+ '"' + dbname+ '"' +""";""")
                self.cursor.execute(create_database)

                print ("DB "+ dbname + " wurde erstellt")

                # baut die Verbindung zu der eben erstellten DB auf
                self.verbindung = psycopg2.connect(dbname=dbname, user=user, password=pw, host=host, port=port)
                cursor = self.verbindung.cursor()
                cursor.execute("""CREATE EXTENSION postgis;""")
                self.connected.autocommit = True

                # liest die Datei (DB_Liste)
                with open(self.file_path, "r", encoding = 'utf-8') as file:
                    self.db_liste = json.load(file)

                # fuegt DB der DB_Liste hinzu
                self.db_liste["items"].update({dbname:{"user": user,"pw": pw, "host":host,"port":port}})

                # speichert die DB_Liste ab
                with open(self.file_path, "w", encoding = 'utf-8') as file:
                    self.db_liste = json.dump(self.db_liste, file, indent=2)

                self.listeFuellen()

                self.label_20.setText("Es hat geklappt :) \nEine neue Datenbank mit dem Namen "+dbname+" wurde erstellt.")
                cursor.close()

            except:
                def showMessage(title, mesage):
                        QMessageBox.information(None, title, mesage)

                showMessage("Warnung", "Die Datenbank " + dbname + " existiert bereits!")

# Reiter 2 - Datensätze laden

    # ausgewählte DB Verbindung löschen
    def dbLoeschen (self):
        if self.listWidget.currentItem() is None:
            def showMessage(title, mesage):
                QMessageBox.information(None, title, mesage)
            showMessage("Warnung", "Keine DB ausgewählt")
        else:
            self.curennt = self.listWidget.currentItem().text()

            with open(self.file_path, "r+", encoding = 'utf-8') as file:
                self.db_liste = json.load(file)

            del self.db_liste['items'][self.curennt]

            for self.curennt in self.file_path:
               self.curennt=None
            with open(self.file_path, "w+", encoding = 'utf-8') as file:
                self.db_liste = json.dump(self.db_liste, file, indent=2)


        # und auch gleich das Listwidget-Fenster aktualisieren
        self.listWidget.clear()

        # liest die Datei (DB_Liste)
        with open(self.file_path, "r", encoding = 'utf-8') as file:
            self.db_liste = json.load(file)

        for item in self.db_liste["items"]:
            self.listWidget.addItem(item)

    # DS in ListWidget_DS anzeigen und nach Auswahl öffnen
    def dsTabelle (self):
        self.listWidget_DS.clear()
        self.listWidget_DS_2.clear()
        self.listWidget_DS_3.clear()
        self.listWidget_spalten.clear()
        self.listWidget_spalten_2.clear()
        self.listWidget_werte.clear()

        # ist das gleiche wie oben def DBverbindung(self)
        if self.listWidget.currentItem() is None:
            def showMessage(title, mesage):
                QMessageBox.information(None, title, mesage)
            showMessage("Warnung", "Keine DB ausgewählt")

        else:
            try:
                curennt = self.listWidget.currentItem().text()
                with open(self.file_path, "r", encoding = 'utf-8') as file:
                    db_liste = json.load(file)

                dbInfo = db_liste['items'][curennt]
                dbname = curennt
                user = dbInfo['user']
                pw = dbInfo['pw']
                host = dbInfo['host']
                port = dbInfo['port']
                conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)

            except:
                def showMessage(title, mesage):
                    QMessageBox.information(None, title, mesage)
                showMessage("Warnung", "Die Datenbank existiert nicht in Postgresql")

        # Zeige mir alle table_schema.table_name
        # in "" ist der SQL Befehl der durch execute ausgeführt wird
            try:
                self.label_8.setText(curennt)
                conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute("""SELECT
                                    table_name
                                FROM
                                    information_schema.tables
                                WHERE
                                    table_type = 'BASE TABLE'
                                AND
                                    table_schema NOT IN ('pg_catalog', 'information_schema');
                            """)

                rows = cur.fetchall()

                for row in rows:
                    self.listWidget_DS.addItems(row)
                    self.listWidget_DS_2.addItems(row)
                    self.listWidget_DS_3.addItems(row)
            except:
                pass
    
    # Tabelle in QGIS laden
    def tabInQGIS (self):

        if self.listWidget.currentItem() is None:
            def showMessage(title, mesage):
                QMessageBox.information(None, title, mesage)
            showMessage("Warnung", "Keine DB ausgewählt!")

        else:
            curennt = self.listWidget.currentItem().text()
            with open(self.file_path, "r", encoding = 'utf-8') as file:
                db_liste = json.load(file)
            dbInfo = db_liste['items'][curennt]
            dbname = curennt
            user = dbInfo['user']
            pw = dbInfo['pw']
            host = dbInfo['host']
            port = dbInfo['port']
            self.conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)

            if self.listWidget_DS.currentItem() is None :
                def showMessage(title, mesage):
                    QMessageBox.information(None, title, mesage)
                showMessage("Warnung", "Kein Datensatz ausgewählt!")
                
            else:
                curennt_ds = self.listWidget_DS.currentItem().text()
                uri = QgsDataSourceUri()

                # set host name, port, database name, username and password
                uri.setConnection(host, str(port), dbname, user, pw)

                # set database schema, table name, geometry column and optionally
                # subset (WHERE clause)

                self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                filter = self.sql.toPlainText()
                try:
                    self.cur.execute("""SELECT geom FROM""" + ' ' + curennt_ds +""";""" )
                    uri.setDataSource( "public", curennt_ds, 'geom', filter)
                    vlayer = QgsVectorLayer(uri.uri(False), curennt_ds, "postgres")
                    QgsProject.instance().addMapLayer(vlayer)
                except:
                    uri.setDataSource( "public", curennt_ds, None, filter)
                    vlayer = QgsVectorLayer(uri.uri(False), curennt_ds, "postgres")
                    QgsProject.instance().addMapLayer(vlayer)
                    
# Reiter 3
                   
    # Tabelle mit SQL Abfrage in QGIS laden
    def tabInQGisAbfrage(self):

        if self.listWidget.currentItem() is None:
            def showMessage(title, mesage):
                QMessageBox.information(None, title, mesage)
            showMessage("Warnung", "Keine DB ausgewählt!")

        else:
            curennt = self.listWidget.currentItem().text()
            with open(self.file_path, "r", encoding = 'utf-8') as file:
                db_liste = json.load(file)
            dbInfo = db_liste['items'][curennt]
            dbname = curennt
            user = dbInfo['user']
            pw = dbInfo['pw']
            host = dbInfo['host']
            port = dbInfo['port']
            self.conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)

            if self.listWidget_DS_2.currentItem() is None :
                def showMessage(title, mesage):
                    QMessageBox.information(None, title, mesage)
                showMessage("Warnung", "Kein Datensatz ausgewählt!")
                
            else:
                curennt_ds = self.listWidget_DS_2.currentItem().text()
                uri = QgsDataSourceUri()
                uri.setConnection(host, str(port), dbname, user, pw)
                self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                filter = self.sql.toPlainText()
                
                try:
                    self.cur.execute("""SELECT geom FROM""" + ' ' + curennt_ds +""";""" )
                    uri.setDataSource( "public", curennt_ds, 'geom', filter)
                    vlayer = QgsVectorLayer(uri.uri(False), curennt_ds, "postgres")
                    QgsProject.instance().addMapLayer(vlayer)
                except:
                    uri.setDataSource( "public", curennt_ds, None, filter)
                    vlayer = QgsVectorLayer(uri.uri(False), curennt_ds, "postgres")
                    QgsProject.instance().addMapLayer(vlayer)
                    
    def testen(self):
        try:
            curennt = self.listWidget.currentItem().text()
            with open(self.file_path, "r", encoding = 'utf-8') as file:
                db_liste = json.load(file)
            dbInfo = db_liste['items'][curennt]
            dbname = curennt
            user = dbInfo['user']
            pw = dbInfo['pw']
            host = dbInfo['host']
            port = dbInfo['port']
            self.conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)
            self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            curennt_ds = self.listWidget_DS_2.currentItem().text()
            filter = self.sql.toPlainText()
            
            try:
                self.cur.execute("""SELECT * FROM """ + ' ' + curennt_ds + """ WHERE """ + filter + """;""" )
                rcount = self.cur.rowcount
                print("%d"%rcount)
                def showMessage(title, mesage):
                    QMessageBox.information(None, title, mesage)
                showMessage("Where - Klausel", "Die Where - Klausel gab   " + "%d"%rcount + "   Zeilen zurück")

            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
                def showMessage(title, mesage):
                    QMessageBox.information(None, title, mesage)
                showMessage("Warnung", "Fehler in SQL - Syntax")
                
        except:
                def showMessage(title, mesage):
                    QMessageBox.information(None, title, mesage)
                showMessage("Warnung", "keine Verbindung zu einer Datenbank")
    
    def tabellenName(self):
        tabelle = self.listWidget_DS_2.currentItem().text()
        self.label_11.setText(tabelle)
        
    def spaltenNameInSqlFenster(self):
        spalten = self.listWidget_spalten.currentItem().text()
        self.sql.insertPlainText(' "' + spalten + '" ')
    
    def spaltenName(self):
        try:
            curennt = self.listWidget.currentItem().text()
            
            with open(self.file_path, "r", encoding = 'utf-8') as file:
                db_liste = json.load(file)
                
            dbInfo = db_liste['items'][curennt]
            dbname = curennt
            user = dbInfo['user']
            pw = dbInfo['pw']
            host = dbInfo['host']
            port = dbInfo['port']
            
            self.conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)
            self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            curennt_ds = self.listWidget_DS_2.currentItem().text()
            self.cur.execute("""SELECT * FROM """ + ' ' + curennt_ds  + """;""" )
            
            spalten = [desc[0] for desc in self.cur.description]
            
            self.listWidget_spalten.clear()
            self.listWidget_spalten.setSortingEnabled(True)
            self.listWidget_spalten.addItems(spalten)
            self.listWidget_werte.clear()
        except:
            self.listWidget_DS_2.clear()
            self.listWidget_spalten.clear()
            self.listWidget_werte.clear()
            def showMessage(title, mesage):
                QMessageBox.information(None, title, mesage)
            showMessage("Warnung", "Sie müssen die richtige Datenbank von bestehende Datenbank Verbindungen (DB-Liste) wählen.")
                
    def werte(self):
        try:
            curennt = self.listWidget.currentItem().text()
            
            with open(self.file_path, "r", encoding = 'utf-8') as file:
                db_liste = json.load(file)
                
            dbInfo = db_liste['items'][curennt]
            dbname = curennt
            user = dbInfo['user']
            pw = dbInfo['pw']
            host = dbInfo['host']
            port = dbInfo['port']
            
            self.conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)
            self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            curennt_ds = self.listWidget_DS_2.currentItem().text()
            spalte_name = self.listWidget_spalten.currentItem().text()
            
            try:
                self.cur.execute(""" SELECT DISTINCT """ + spalte_name + """ FROM """ + ' ' + curennt_ds  + """ ORDER BY """ + spalte_name + """;""" )
                result = self.cur.fetchall()
                self.listWidget_werte.clear()  
                for wert in result:        
                    self.listWidget_werte.addItems(wert)
                    
            except:
                self.cur.execute(""" SELECT DISTINCT """ + spalte_name + """ FROM """ + ' ' + curennt_ds  + """ ORDER BY """ + spalte_name + """;""" )
                result = self.cur.fetchall()
                self.listWidget_werte.clear()
                
                result2 = [str(item)[1:-1].replace("Decimal('", '') for item in result]
                result3 = [[item.replace("')", '')] for item in result2]
                for wert in result3:        
                    self.listWidget_werte.addItems(wert) 
                
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            self.listWidget_spalten.clear()
            self.listWidget_werte.clear()
            def showMessage(title, mesage):
                QMessageBox.information(None, title, mesage)
            showMessage("Warnung", "Sie müssen die richtige Datenbank von bestehende Datenbank Verbindungen (DB-Liste) wählen.")
        
    def werteInSqlFenster(self):
        werte = self.listWidget_werte.currentItem().text()
        self.sql.insertPlainText(" '" + werte + "' ")
    
    def gleich(self):
        self.sql.insertPlainText(" = ")
        
    def ungleich(self):
        self.sql.insertPlainText(" != ")
        
    def kleiner(self):
        self.sql.insertPlainText(" < ")
    
    def groesser(self):
        self.sql.insertPlainText(" > ")
        
    def prozent(self):
        self.sql.insertPlainText(" % ")
        
    def operatorIN(self):
        self.sql.insertPlainText(" IN ")  
        
    def notIN(self):
        self.sql.insertPlainText(" NOT IN ")
        
    def operatorLike(self):
        self.sql.insertPlainText(" LIKE ") 
    
    def klammerAuf(self):
        self.sql.insertPlainText(" ( ")
    
    def klammerZu(self):
        self.sql.insertPlainText(" ) ")
    
    def operatorAnd(self):
        self.sql.insertPlainText(" AND ")
    
    def operatorNot(self):
        self.sql.insertPlainText(" NOT ")
        
    def operatorOr(self):
        self.sql.insertPlainText(" OR ")
    
    def kleinerOderGleich(self):
        self.sql.insertPlainText(" <= ")
    
    def groesserOderGleich(self):
        self.sql.insertPlainText(" >= ")

# Reiter 4    

    def selektierenPostGis(self):
        try:
            curennt = self.listWidget.currentItem().text()
            with open(self.file_path, "r", encoding = 'utf-8') as file:
                db_liste = json.load(file)
            dbInfo = db_liste['items'][curennt]
            dbname = curennt
            user = dbInfo['user']
            pw = dbInfo['pw']
            host = dbInfo['host']
            port = dbInfo['port']
            self.conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)
            self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                 
            try:
                postGisAbfrage = self.postgis.toPlainText()
                comand = ("""  """ + postGisAbfrage +  """;""" )
                
                self.cur.execute(comand)           
                result = self.cur.fetchall()
                header = [desc[0] for desc in self.cur.description]
                
                self.tableWidget.setRowCount(0)
                self.tableWidget.setColumnCount(len(header))
                self.tableWidget.setHorizontalHeaderLabels(header)
                                
                for row_number, row_data in enumerate(result):
                    self.tableWidget.insertRow(row_number)
                    for column_number, data in enumerate(row_data):
                        self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(str(data)))

                self.cur.close()
                self.conn.commit()
                
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
                def showMessage(title, mesage):
                    QMessageBox.information(None, title, mesage)
                showMessage("Warnung", "Fehler in SQL - Syntax. Sie können die Fehler in Pythonfenster sehen")
                
        except:
            def showMessage(title, mesage):
                QMessageBox.information(None, title, mesage)
            showMessage("Warnung", "keine Verbindung zu einer Datenbank")
                
    def ausfuehrenPostGis(self):
        
        postGisAbfrage = self.postgis.toPlainText()
        comand = ( """ """ + postGisAbfrage + """ """)
        conn = None
        try:
            curennt = self.listWidget.currentItem().text()
            with open(self.file_path, "r", encoding = 'utf-8') as file:
                db_liste = json.load(file)
            dbInfo = db_liste['items'][curennt]
            dbname = curennt
            user = dbInfo['user']
            pw = dbInfo['pw']
            host = dbInfo['host']
            port = dbInfo['port']
            self.conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)
            self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            self.tableWidget.setRowCount(1)
            self.cur.execute(comand)
            message = self.cur.statusmessage
            self.tableWidget.setItem(0, 0, QTableWidgetItem(message))
            
            self.cur.close()
            self.conn.commit()
            self.dsTabelle()
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            def showMessage(title, mesage):
                QMessageBox.information(None, title, mesage)
            showMessage("Warnung", "Fehler in SQL - Syntax. Sie können die Fehler in Pythonfenster sehen")           
    
    def spaltenName2(self):
        try:
            curennt = self.listWidget.currentItem().text()
            
            with open(self.file_path, "r", encoding = 'utf-8') as file:
                db_liste = json.load(file)
                
            dbInfo = db_liste['items'][curennt]
            dbname = curennt
            user = dbInfo['user']
            pw = dbInfo['pw']
            host = dbInfo['host']
            port = dbInfo['port']
            
            self.conn = psycopg2.connect(database=dbname, user=user, password=pw, host=host, port=port)
            self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            curennt_ds = self.listWidget_DS_3.currentItem().text()
            self.cur.execute("""SELECT * FROM """ + ' ' + curennt_ds  + """;""" )
            
            spalten = [desc[0] for desc in self.cur.description]
            
            self.listWidget_spalten_2.clear()
            self.listWidget_spalten_2.setSortingEnabled(True)
            self.listWidget_spalten_2.addItems(spalten)
        except:
            self.listWidget_DS_3.clear()
            self.listWidget_spalten_2.clear()
            def showMessage(title, mesage):
                QMessageBox.information(None, title, mesage)
            showMessage("Warnung", "Sie müssen die richtige Datenbank von bestehende Datenbank Verbindungen (DB-Liste) wählen.")
    
    def tabellenNameInPostgis(self):
        tabelle = self.listWidget_DS_3.currentItem().text()
        self.postgis.insertPlainText( tabelle + " ")
        
    def spaltenNameInPostgis(self):
        spalten = self.listWidget_spalten_2.currentItem().text()
        self.postgis.insertPlainText('"' + spalten + '"')
        
    def postGisFunctionName(self):
        if self.treeWidget.currentItem().text(0) == 'Geometry Constructors':
            pass
            
        elif self.treeWidget.currentItem().text(0) == 'Geometry Accessors':
            pass
        
        elif self.treeWidget.currentItem().text(0) == 'Geometry Editors':
            pass
        
        elif self.treeWidget.currentItem().text(0) == 'Geometry Outputs':
            pass
        
        elif self.treeWidget.currentItem().text(0) == 'Spatial Relationships':
            pass
        
        elif self.treeWidget.currentItem().text(0) == 'Geometry Processing':
            pass
        
        elif self.treeWidget.currentItem().text(0) == 'Linear Referencing':
            pass
        
        elif self.treeWidget.currentItem().text(0) == 'Temporal Support':
            pass
            
        elif self.treeWidget.currentItem().text(0) == 'Miscellaneous Functions':
            pass    
            
        else:
            function = self.treeWidget.currentItem().text(0)
            self.postgis.insertPlainText( function + "( ")
        
    def helpPostgis(self):
        self.label_17.clear()       
        
        if self.treeWidget.currentItem().text(0) == 'UpdateGeometrySRID':
            self.label_17.setText("""UpdateGeometrySRID
            
Updates the SRID of all features in a geometry column,geometry_columns metadata and srid. 
If itwas enforced with constraints,the constraints will be updated with new srid constraint. 
If the old was enforced by type definition, the type definition will be changed.

Synopsis
text UpdateGeometrySRID(varchar table_name, varchar column_name, integer srid);
text UpdateGeometrySRID(varchar schema_name, varchar table_name, varchar column_name, integer srid);
text UpdateGeometrySRID(varchar catalog_name, varchar schema_name, varchar table_name, varchar column_name, integer srid);
            
Examples:
SELECT UpdateGeometrySRID('roads','geom',4326);""")
           
        elif self.treeWidget.currentItem().text(0) == 'ST_BdPolyFromText':
            self.label_17.setText("""ST_BdPolyFromText
            
Description
Construct a Polygon given an arbitrary collection of closed linestrings as a MultiLineString Well-Known text representation.

Synopsis
geometry ST_BdPolyFromText(text WKT, integer srid);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_Box2dFromGeoHash':
            self.label_17.setText("""ST_Box2dFromGeoHash 

Description
Return a BOX2D from a GeoHash string.
If no precision is specficified ST_Box2dFromGeoHash returns a BOX2D based on full precision of the input GeoHash string.
If precision is specified ST_Box2dFromGeoHash will use that many characters from the GeoHash to create the BOX2D.
Lower precision values results in larger BOX2Ds and larger values increase the precision.

Synopsis
box2d ST_Box2dFromGeoHash(text geohash, integer precision=full_precision_of_geohash);

Examples
SELECT ST_Box2dFromGeoHash('9qqj7nmxncgyy4d0dbxqz0');""") 
       
        elif self.treeWidget.currentItem().text(0) == 'ST_BdMPolyFromText':
            self.label_17.setText("""ST_BdMPolyFromText

Description
Construct a Polygon given an arbitrary collection of closed linestrings, polygons, MultiLineStrings as Well-Known text representation.

Synopsis
geometry ST_BdMPolyFromText(text WKT, integer srid);

Synopsis
geometry ST_BdMPolyFromText(text WKT, integer srid);""")  
          
        elif self.treeWidget.currentItem().text(0) == 'ST_GeogFromText':
            self.label_17.setText("""ST_GeogFromText 

Description
Returns a geography object from the well-known text or extended well-known representation. SRID 4326 is assumed if unspecified.
This is an alias for ST_GeographyFromText. Points are always expressed in long lat form.

Synopsis
geography ST_GeogFromText(text EWKT);

Examples
--- converting lon lat coords to geography
ALTER TABLE sometable 
ADD COLUMN geog geography(POINT,4326);
UPDATE sometable SET geog = ST_GeogFromText('SRID=4326;POINT(' || lon || ' ' || lat || ')'); """)
        
        elif self.treeWidget.currentItem().text(0) == 'ST_GeographyFromText':
            self.label_17.setText("""ST_GeographyFromText

Description
Returns a geography object from the well-known text representation. SRID 4326 is assumed if unspecified. 


Synopsis
geography ST_GeographyFromText(text EWKT);""")    

        elif self.treeWidget.currentItem().text(0) == 'ST_GeogFromWKB':
            self.label_17.setText("""ST_GeogFromWKB
            
Description
The ST_GeogFromWKB function, takes a well-known binary representation (WKB) of a geometry or PostGIS Extended WKB and creates an instance of the appropriate geography type. This function plays the role of the Geometry Factory in SQL. If SRID is not specified, it defaults to 4326 (WGS 84 long lat).

Synopsis
geography ST_GeogFromWKB(bytea wkb);

Examples
SELECT ST_AsText(
ST_GeogFromWKB(E'\\001\\002\\000\\000\\000\\002\\000\\000\\000\\ 037\\205\\353Q\\270~\\\\\300\\323Mb\\020X\\231C@\\020X9\\264\\310~\\\\\\300)\\\\\\217\\302\\365\\230C@'));""")
        
        elif self.treeWidget.currentItem().text(0) == 'ST_GeomFromTWKB':
            self.label_17.setText("""ST_GeomFromTWKB

Description
The ST_GeomFromTWKB function, takes a a TWKB ("Tiny Well-Known Binary") geometry representation (WKB) and creates an instance of the appropriate geometry type.

Synopsis
geometry ST_GeomFromTWKB(bytea twkb);

Examples
SELECT ST_AsText(ST_GeomFromTWKB(ST_AsTWKB(
'LINESTRING(126 34, 127 35)'::geometry))); """)           
        
        elif self.treeWidget.currentItem().text(0) == 'ST_GeomCollFromText':
            self.label_17.setText("""ST_GeomCollFromText
                    
Description
Makes a collection Geometry from the Well-Known-Text (WKT) representation with the given SRID. If SRID is not give, it defaults to 0.
OGC SPEC 3.2.6.2 - option SRID is from the conformance suite Returns null if the WKT is not a GEOMETRYCOLLECTION        

Synopsis
geometry ST_GeomCollFromText(text WKT, integer srid);
geometry ST_GeomCollFromText(text WKT);
        
Examples
SELECT ST_GeomCollFromText( 'GEOMETRYCOLLECTION(POINT(1 2),LINESTRING(1 2, 3 4))');""")        
        
        elif self.treeWidget.currentItem().text(0) == 'ST_GeomFromEWKB':
            self.label_17.setText("""ST_GeomFromEWKB
            
Description
Constructs a PostGIS ST_Geometry object from the OGC Extended Well-Known binary (EWKT) representation.

Synopsis
geometry ST_GeomFromEWKB(bytea EWKB);

Examples
SELECT ST_GeomFromEWKB(E'\\001\\002\\000\\000\\255\\020\\000\\000\\003\\ 000\\000\\000\\344J=\\013B\\312Q\\300n\\303(\\010\\036!E@''\\277E''K\\312Q\\300\\366{b\\235*!E@\\225|\\354.P\\312Q\\300p\\231\\323e1!E@');""")

        elif self.treeWidget.currentItem().text(0) == 'ST_GeomFromEWKT':
            self.label_17.setText("""ST_GeomFromEWKT
            
Description
Constructs a PostGIS ST_Geometry object from the OGC Extended Well-Known text (EWKT) representation.

Synopsis
geometry ST_GeomFromEWKT(text EWKT);

SELECT ST_GeomFromEWKT('SRID=4269;LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)');

SELECT ST_GeomFromEWKT('SRID=4269;MULTILINESTRING((-71.160281 42.258729,-71.160837  42.259113,-71.161144 42.25932))'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_GeometryFromText':
            self.label_17.setText("""ST_GeometryFromText
            
ST_GeometryFromText—Return a specified ST_Geometry value fromWell-Known Text representation (WKT). This is an alias name for ST_GeomFromText            
            
Synopsis
geometry ST_GeometryFromText(text WKT);
geometry ST_GeometryFromText(text WKT, integer srid);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_GeomFromGeoHash':
            self.label_17.setText("""ST_GeomFromGeoHash
            
Description
Return a geometry from a GeoHash string. The geometry will be a polygon representing the GeoHash bounds.
If no precision is specified ST_GeomFromGeoHash returns a polygon based on full precision of the input GeoHash string.
If precision is specified ST_GeomFromGeoHash will use that many characters from the GeoHash to create the polygon.            

Synopsis
geometry ST_GeomFromGeoHash(text geohash, integer precision=full_precision_of_geohash);

Examples
SELECT ST_AsText(ST_GeomFromGeoHash('9qqj7nmxncgyy4d0dbxqz0'));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_GeomFromGML':
            self.label_17.setText("""ST_GeomFromGML

Description
Constructs a PostGIS ST_Geometry object from the OGC GML representation.
ST_GeomFromGML works only for GML Geometry fragments. It throws an error if you try to use it on a whole GML document.
OGC GML versions supported:
• GML 3.2.1 Namespace
• GML 3.1.1 Simple Features profile SF-2 (with GML 3.1.0 and 3.0.0 backward compatibility)
• GML 2.1.2

Synopsis
geometry ST_GeomFromGML(text geomgml);
geometry ST_GeomFromGML(text geomgml, integer srid);

Examples - A single geometry with srsName
SELECT ST_GeomFromGML('
<gml:LineString srsName="EPSG:4269">
<gml:coordinates>
-71.16028,42.258729 -71.160837,42.259112 -71.161143,42.25932
</gml:coordinates>
</gml:LineString>');""")            
            
        elif self.treeWidget.currentItem().text(0) == 'ST_GeomFromGeoJSON':
            self.label_17.setText("""ST_GeomFromGeoJSON

Description
Constructs a PostGIS geometry object from the GeoJSON representation.
ST_GeomFromGeoJSON works only for JSON Geometry fragments. It throws an error if you try to use it on a whole JSON document.

Synopsis
geometry ST_GeomFromGeoJSON(text geomjson);

Examples
SELECT ST_AsText(ST_GeomFromGeoJSON('{"type":"Point","coordinates":[-48.23456,20.12345]}')) As wkt;

-- a 3D linestring
SELECT ST_AsText(ST_GeomFromGeoJSON('{"type":"LineString", "coordinates":[[1,2,3],[4,5,6],[7,8,9]]}')) As wkt;""")

        elif self.treeWidget.currentItem().text(0) == 'ST_GeomFromKML':
            self.label_17.setText("""ST_GeomFromKML

Description
Constructs a PostGIS ST_Geometry object from the OGC KML representation.
ST_GeomFromKML works only for KML Geometry fragments. It throws an error if you try to use it on a whole KML document.

Synopsis
geometry ST_GeomFromKML(text geomkml);

Examples - A single geometry with srsName
SELECT ST_GeomFromKML(' <LineString>
<coordinates>-71.1663,42.2614
-71.1667,42.2616</coordinates></LineString>'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_GMLToSQL':
            self.label_17.setText("""ST_GMLToSQL

Return a specified ST_Geometry value from GML representation. This is an alias name for ST_GeomFromGML            

Synopsis
geometry ST_GMLToSQL(text geomgml);
geometry ST_GMLToSQL(text geomgml, integer srid);

Synopsis
geometry ST_GMLToSQL(text geomgml);
geometry ST_GMLToSQL(text geomgml, integer srid);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_GeomFromText':
            self.label_17.setText("""ST_GeomFromText
            
Return a specified ST_Geometry value from Well-Known Text representation (WKT).

Synopsis
geometry ST_GeomFromText(text WKT);
geometry ST_GeomFromText(text WKT, integer srid);

Examples
SELECT ST_GeomFromText('LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)');

SELECT ST_GeomFromText('MULTILINESTRING((-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932))');   

SELECT ST_GeomFromText('POINT(-71.064544 42.28787)');

SELECT ST_GeomFromText('POLYGON((-71.1776585052917 42.3902909739571,-71.1776820268866 42.3903701743239, -71.1776063012595 42.3903825660754,-71.1775826583081 42.3903033653531,-71.1776585052917 42.3902909739571))');""")

        elif self.treeWidget.currentItem().text(0) == 'ST_GeomFromWKB':
            self.label_17.setText("""ST_GeomFromWKB
            
Description
The ST_GeomFromWKB function, takes a well-known binary representation of a geometry and a Spatial Reference System ID (SRID) and creates an instance of the appropriate geometry type. This function plays the role of the Geometry Factory in SQL. This is an alternate name for ST_WKBToSQL.
If SRID is not specified, it defaults to 0 (Unknown).            

Synopsis
geometry ST_GeomFromWKB(bytea geom);
geometry ST_GeomFromWKB(bytea geom, integer srid);

Examples
SELECT ST_AsText( ST_GeomFromWKB( ST_AsEWKB( 
'POINT(2 5)'::geometry))); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_LineFromEncodedPolyline':
            self.label_17.setText("""ST_LineFromEncodedPolyline
            
Creates a LineString from an Encoded Polyline.

Synopsis
geometry ST_LineFromEncodedPolyline(text polyline, integer precision=5);

Examples
SELECT ST_AsEWKT(ST_LineFromEncodedPolyline('_p~iF~ps|U_ulLnnqC_mqNvxq‘@'));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_LineFromMultiPoint':
            self.label_17.setText("""ST_LineFromMultiPoint

Creates a LineString from a MultiPoint geometry.

Synopsis
geometry ST_LineFromMultiPoint(geometry aMultiPoint);

Examples
--Create a 3d line string from a 3d multipoint
SELECT ST_AsEWKT(ST_LineFromMultiPoint(ST_GeomFromEWKT('MULTIPOINT(1 2 3, 4 5 6, 7 8 9)')));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_LineFromText':
            self.label_17.setText("""ST_LineFromText
            
Description
Makes a Geometry from WKT with the given SRID. If SRID is not give, it defaults to 0. If WKT passed in is not a LINESTRING, then null is returned.

Synopsis
geometry ST_LineFromText(text WKT);
geometry ST_LineFromText(text WKT, integer srid);

Examples
SELECT ST_LineFromText('LINESTRING(1 2, 3 4)') AS aline, ST_LineFromText('POINT(1 2)') AS null_return;""")

        elif self.treeWidget.currentItem().text(0) == 'ST_LineFromWKB':
            self.label_17.setText("""ST_LineFromWKB

Description
The ST_LineFromWKB function, takes a well-known binary representation of geometry and a Spatial Reference System ID (SRID) and creates an instance of the appropriate geometry type - in this case, a LINESTRING geometry. This function plays the role of the Geometry Factory in SQL.
If an SRID is not specified, it defaults to 0. NULL is returned if the input bytea does not represent a LINESTRING.

Synopsis
geometry ST_LineFromWKB(bytea WKB);
geometry ST_LineFromWKB(bytea WKB, integer srid);

Examples
SELECT ST_LineFromWKB(ST_AsBinary(ST_GeomFromText('LINESTRING(
1 2, 3 4)'))) AS aline, ST_LineFromWKB(ST_AsBinary( ST_GeomFromText('POINT(1 2)'))) IS NULL AS null_return;""")


        elif self.treeWidget.currentItem().text(0) == 'ST_LinestringFromWKB':
            self.label_17.setText("""ST_LinestringFromWKB
            
Description
The ST_LinestringFromWKB function, takes a well-known binary representation of geometry and a Spatial Reference System ID (SRID) and creates an instance of the appropriate geometry type - in this case, a LINESTRING geometry. This function plays the role of the Geometry Factory in SQL.
If an SRID is not specified, it defaults to 0. NULL is returned if the input bytea does not represent a LINESTRING geometry.
This an alias for ST_LineFromWKB.            

Synopsis
geometry ST_LinestringFromWKB(bytea WKB);
geometry ST_LinestringFromWKB(bytea WKB, integer srid);

Examples
SELECT ST_LineStringFromWKB(ST_AsBinary(ST_GeomFromText( 'LINESTRING(1 2, 3 4)'))) AS aline, ST_LinestringFromWKB(ST_AsBinary(ST_GeomFromText( 
'POINT(1 2)'))) IS NULL AS null_return; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_MakeBox2D':
            self.label_17.setText("""ST_MakeBox2D
            
Description
Creates a BOX2D defined by the given point geometries. This is useful for doing range queries

Synopsis
box2d ST_MakeBox2D(geometry pointLowLeft, geometry pointUpRight);

Examples
--Return all features that fall reside or partly reside in a US national atlas coordinate bounding box
--It is assumed here that the geometries are stored with SRID = 2163 (US National atlas equal area)     

SELECT feature_id, feature_name, the_geom 
FROM features
WHERE the_geom && ST_SetSRID(ST_MakeBox2D(ST_Point(-989502.1875, 528439.5625), ST_Point(-987121.375 ,529933.1875)),2163) """)      

        elif self.treeWidget.currentItem().text(0) == 'ST_3DMakeBox':
            self.label_17.setText("""ST_3DMakeBox
            
Creates a BOX3D defined by the given 3d point geometries.

Synopsis
box3d ST_3DMakeBox(geometry point3DLowLeftBottom, geometry point3DUpRightTop);

Examples
SELECT ST_3DMakeBox(ST_MakePoint(-989502.1875, 528439.5625,10),
ST_MakePoint(-987121.375 ,529933.1875, 10)) As abb3d""") 

        elif self.treeWidget.currentItem().text(0) == 'ST_MakeLine':
            self.label_17.setText("""ST_MakeLine

Description
ST_MakeLine comes in 3 forms: a spatial aggregate that takes rows of point, multipoint, or line geometries and returns a line string, a function that takes an array of point, multipoint, or line, and a regular function that takes two point, multipoint, or line geometries. You might want to use a subselect to order points before feeding them to the aggregate version of this function.
Inputs other than point, multipoint, or lines are ignored. When adding line components common nodes at the beginning of lines are removed from the output. Common nodes in point and multipoint inputs are not removed.

Synopsis
geometry ST_MakeLine(geometry set geoms);
geometry ST_MakeLine(geometry geom1, geometry geom2);
geometry ST_MakeLine(geometry[ ] geoms_array);

Examples: Spatial Aggregate version
This example takes a sequence of GPS points and creates one record for each gps travel where the geometry field is a line string composed of the gps points in the order of the travel.

SELECT gps.gps_track, ST_MakeLine(gps.the_geom) As newgeom FROM (SELECT gps_track,gps_time, the_geom FROM gps_points ORDER BY gps_track, gps_time) As gps GROUP BY gps.gps_track;

Examples: Non-Spatial Aggregate version
First example is a simple one off line string composed of 2 points. The second formulates line strings from 2 points a user draws. The third is a one-off that joins 2 3d points to create a line in 3d space.      
  
SELECT ST_AsText(ST_MakeLine(ST_MakePoint(1,2), ST_MakePoint(3,4)));

SELECT userpoints.id, ST_MakeLine(startpoint, endpoint) As drawn_line FROM userpoints ;

SELECT ST_AsEWKT(ST_MakeLine(ST_MakePoint(1,2,3), ST_MakePoint(3,4,5)));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_MakeEnvelope':
            self.label_17.setText("""ST_MakeEnvelope
            
Description
Creates a rectangular Polygon formed from the minima and maxima. by the given shell. Input values must be in SRS specified by the SRID. If no SRID is specified the unknown spatial reference system is assumed            

Synopsis
geometry ST_MakeEnvelope(double precision xmin, double precision ymin, double precision xmax, double precision ymax, integer srid=unknown);

Example: Building a bounding box polygon
SELECT ST_AsText(ST_MakeEnvelope(10, 10, 11, 11, 4326));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_MakePolygon':
            self.label_17.setText("""ST_MakePolygon
            
Description
Creates a Polygon formed by the given shell. Input geometries must be closed LINESTRINGS. Comes in 2 variants. 
Variant 1: Takes one closed linestring.
Variant 2: Creates a Polygon formed by the given shell and array of holes. You can construct a geometry array using ST_Accum or the PostgreSQL ARRAY[] and ARRAY() constructs. Input geometries must be closed LINESTRINGS.        

Synopsis
geometry ST_MakePolygon(geometry linestring);
geometry ST_MakePolygon(geometry outerlinestring, geometry[] interiorlinestrings);

Examples: Single closed LINESTRING
--2d line
SELECT ST_MakePolygon(ST_GeomFromText('LINESTRING(75.15 29.53,77 29,77.6 29.5, 75.15 29.53)'));

--If linestring is not closed
--you can add the start point to close it
SELECT ST_MakePolygon(ST_AddPoint(foo.open_line, ST_StartPoint(foo.open_line)))
FROM (SELECT ST_GeomFromText('LINESTRING(75.15 29.53,77 29,77.6 29.5)') As open_line) As foo;

--3d closed line
SELECT ST_MakePolygon(ST_GeomFromText('LINESTRING(75.15 29.53 1,77 29 1,77.6 29.5 1, 75.15 29.53 1)'));

Examples: Outer shell with inner shells
SELECT ST_MakePolygon( ST_ExteriorRing(ST_Buffer(foo.line,10)),
ARRAY[ST_Translate(foo.line,1,1), ST_ExteriorRing(ST_Buffer(ST_MakePoint(20,20),1)) ])
FROM (SELECT ST_ExteriorRing(ST_Buffer(ST_MakePoint(10,10),10,10)) As line ) As foo;""")

        elif self.treeWidget.currentItem().text(0) == 'ST_MakePoint':
            self.label_17.setText("""ST_MakePoint
            
Description
Creates a 2D,3DZ or 4D point geometry (geometry with measure). ST_MakePoint while not being OGC compliant is generally faster and more precise than ST_GeomFromText and ST_PointFromText. It is also easier to use if you have raw coordinates rather than WKT.
  
Synopsis
geometry ST_MakePoint(double precision x, double precision y);
geometry ST_MakePoint(double precision x, double precision y, double precision z);
geometry ST_MakePoint(double precision x, double precision y, double precision z, double precision m);  
  
Examples
--Return point with unknown SRID
SELECT ST_MakePoint(-71.1043443253471, 42.3150676015829);

--Return point marked as WGS 84 long lat
SELECT ST_SetSRID(ST_MakePoint(-71.1043443253471, 42.3150676015829),4326);

--Return a 3D point (e.g. has altitude)
SELECT ST_MakePoint(1, 2,1.5);

--Get z of point
SELECT ST_Z(ST_MakePoint(1, 2,1.5)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_MakePointM':
            self.label_17.setText("""ST_MakePointM
            
Creates a point geometry with an x y and m coordinate.    

Synopsis
geometry ST_MakePointM(float x, float y, float m);        
            
Examples
We use ST_AsEWKT in these examples to show the text representation instead of ST_AsText because ST_AsText does not support returning M.
--Return EWKT representation of point with unknown SRID
SELECT ST_AsEWKT(ST_MakePointM(-71.1043443253471, 42.3150676015829, 10));     

--Return EWKT representation of point with measure marked as WGS 84 long lat
SELECT ST_AsEWKT(ST_SetSRID(ST_MakePointM(-71.1043443253471, 42.3150676015829,10),4326));

--Return a 3d point (e.g. has altitude)
SELECT ST_MakePoint(1, 2,1.5);

--Get m of point
SELECT ST_M(ST_MakePointM(-71.1043443253471, 42.3150676015829,10));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_MLineFromText':
            self.label_17.setText("""ST_MLineFromText
            
Description
Makes a Geometry from Well-Known-Text (WKT) with the given SRID. If SRID is not give, it defaults to 0. OGC SPEC 3.2.6.2 - option SRID is from the conformance suite Returns null if the WKT is not a MULTILINESTRING       

Synopsis
geometry ST_MLineFromText(text WKT, integer srid);
geometry ST_MLineFromText(text WKT);
            
Examples
SELECT ST_MLineFromText('MULTILINESTRING((1 2, 3 4), (4 5, 6 7))');""")            
            
        elif self.treeWidget.currentItem().text(0) == 'ST_MPointFromText':
            self.label_17.setText("""ST_MPointFromText    
            
Description
Makes a Geometry from WKT with the given SRID. If SRID is not give, it defaults to 0. OGC SPEC 3.2.6.2 - option SRID is from the conformance suite Returns null if the WKT is not a MULTIPOINT            

Synopsis
geometry ST_MPointFromText(text WKT, integer srid);
geometry ST_MPointFromText(text WKT);
            
Examples
SELECT ST_MPointFromText('MULTIPOINT(1 2, 3 4)');
SELECT ST_MPointFromText('MULTIPOINT(-70.9590 42.1180, -70.9611 42.1223)', 4326);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_MPolyFromText':
            self.label_17.setText("""ST_MPolyFromText
            
Description
Makes a MultiPolygon from WKT with the given SRID. If SRID is not give, it defaults to 0. OGC SPEC 3.2.6.2 - option SRID is from the conformance suite Throws an error if the WKT is not a MULTIPOLYGON            

Synopsis
geometry ST_MPolyFromText(text WKT, integer srid);
geometry ST_MPolyFromText(text WKT);
            
Examples
SELECT ST_MPolyFromText('MULTIPOLYGON(((0 0 1,20 0 1,20 20 1,0 20 1,0 0 1),(5 5 3,5 7 3,7 7 3,7 5 3,5 5 3)))');""")

        elif self.treeWidget.currentItem().text(0) == 'ST_Point':
            self.label_17.setText("""ST_Point

Description
Returns an ST_Point with the given coordinate values. MM compliant alias for ST_MakePoint that takes just an x and y.            

Synopsis
geometry ST_Point(float x_lon, float y_lat);

Examples: Geometry
SELECT ST_SetSRID(ST_Point(-71.1043443253471, 42.3150676015829),4326)

Examples: Geography
SELECT CAST(ST_SetSRID(ST_Point(-71.1043443253471, 42.3150676015829),4326) As geography);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_PointFromGeoHash':
            self.label_17.setText("""ST_PointFromGeoHash
            
Description
Return a point from a GeoHash string. The point represents the center point of the GeoHash. If no precision is specified ST_PointFromGeoHash returns a point based on full precision of the input GeoHash string. If precision is specified ST_PointFromGeoHash will use that many characters from the GeoHash to create the point.

Synopsis
point ST_PointFromGeoHash(text geohash, integer precision=full_precision_of_geohash);

Examples
SELECT ST_AsText(ST_PointFromGeoHash('9qqj7nmxncgyy4d0dbxqz0'));
SELECT ST_AsText(ST_PointFromGeoHash('9qqj7nmxncgyy4d0dbxqz0', 4));
SELECT ST_AsText(ST_PointFromGeoHash('9qqj7nmxncgyy4d0dbxqz0', 10));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_PointFromText':
            self.label_17.setText("""ST_PointFromText
        
Description
Constructs a PostGIS ST_Geometry point object from the OGC Well-Known text representation. If SRID is not give, it defaults to unknown (currently 0). If geometry is not a WKT point representation, returns null. If completely invalid WKT, then throws an error.

Synopsis
geometry ST_PointFromText(text WKT);
geometry ST_PointFromText(text WKT, integer srid);

Examples
SELECT ST_PointFromText('POINT(-71.064544 42.28787)');
SELECT ST_PointFromText('POINT(-71.064544 42.28787)', 4326);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_PointFromWKB':
            self.label_17.setText("""ST_PointFromWKB

Description
The ST_PointFromWKB function, takes a well-known binary representation of geometry and a Spatial Reference System ID (SRID) and creates an instance of the appropriate geometry type - in this case, a POINT geometry. This function plays the role of the Geometry Factory in SQL.
If an SRID is not specified, it defaults to 0. NULL is returned if the input bytea does not represent a POINT geometry.

Synopsis
geometry ST_GeomFromWKB(bytea geom);
geometry ST_GeomFromWKB(bytea geom, integer srid);

Examples
SELECT ST_AsText(ST_PointFromWKB(ST_AsEWKB( 
'POINT(2 5)'::geometry)));

SELECT ST_AsText(ST_PointFromWKB(ST_AsEWKB( 
'LINESTRING(2 5, 2 6)'::geometry)));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_Polygon':
            self.label_17.setText("""ST_Polygon
            
Returns a polygon built from the specified linestring and SRID.

Synopsis
geometry ST_Polygon(geometry aLineString, integer srid);

Examples
--a 2d polygon
SELECT ST_Polygon(ST_GeomFromText('LINESTRING(75.15 29.53,77 29,77.6 29.5, 75.15 29.53)'), 4326);
--a 3d polygon
SELECT ST_AsEWKT(ST_Polygon(ST_GeomFromEWKT('LINESTRING(75.15 29.53 1,77 29 1,77.6 29.5 1, 75.15 29.53 1)'), 4326));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_PolygonFromText':
            self.label_17.setText("""ST_PolygonFromText
            
Description
Makes a Geometry from WKT with the given SRID. If SRID is not give, it defaults to 0. Returns null if WKT is not a polygon. OGC SPEC 3.2.6.2 - option SRID is from the conformance suite

Synopsis
geometry ST_PolygonFromText(text WKT);
geometry ST_PolygonFromText(text WKT, integer srid);

Examples
SELECT ST_PolygonFromText('POLYGON((-71.1776585052917 42.3902909739571,-71.1776820268866 42.3903701743239, -71.1776063012595 42.3903825660754,-71.1775826583081 42.3903033653531,-71.1776585052917 42.3902909739571))');""")

        elif self.treeWidget.currentItem().text(0) == 'ST_WKBToSQL':
            self.label_17.setText("""ST_WKBToSQL
            
Return a specified ST_Geometry value from Well-Known Binary representation (WKB). This is an alias name for ST_GeomFromWKB that takes no srid

Synopsis
geometry ST_WKBToSQL(bytea WKB);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_WKTToSQL':
            self.label_17.setText("""ST_WKTToSQL

Return a specified ST_Geometry value fromWell-Known Text representation (WKT). This is an alias name for ST_GeomFromText

Synopsis
geometry ST_WKTToSQL(text WKT);""")
#8.5 Geometry Accessors
        elif self.treeWidget.currentItem().text(0) == 'GeometryType':
            self.label_17.setText("""GeometryType
            
Description
Returns the type of the geometry as a string. Eg: 'LINESTRING', 'POLYGON', 'MULTIPOINT', etc.
OGC SPEC s2.1.1.1 - Returns the name of the instantiable subtype of Geometry of which this Geometry instance is a member.
The name of the instantiable subtype of Geometry is returned as a string.        

Synopsis
text GeometryType(geometry geomA);

Examples
SELECT GeometryType(ST_GeomFromText('LINESTRING(77.29 29.07,77.42 29.26,77.27 29.31,77.29 29.07)'));""")
        
        elif self.treeWidget.currentItem().text(0) == 'ST_Boundary':
            self.label_17.setText("""ST_Boundary
            
Description
Returns the closure of the combinatorial boundary of this Geometry. The combinatorial boundary is defined as described in section 3.12.3.2 of the OGC SPEC. Because the result of this function is a closure, and hence topologically closed, the resulting boundary can be represented using representational geometry primitives as discussed in the OGC SPEC, section 3.12.2.            
 
Synopsis
geometry ST_Boundary(geometry geomA);
 
Examples
SELECT ST_Boundary(geom) FROM (SELECT 'LINESTRING(100 150,50 60,70 80, 160 170)'::geometry As geom) As f;     
SELECT ST_Boundary(geom)
FROM (SELECT 'POLYGON (( 10 130, 50 190, 110 190, 140 150, 150 80, 100 10, 20 40, 10 130 ),( 70 40, 100 50, 120 80, 80 110,  50 90, 70 40 ))'::geometry As geom) As f; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_CoordDim':
            self.label_17.setText("""ST_CoordDim

Description
Return the coordinate dimension of the ST_Geometry value. This is the MM compliant alias name for ST_NDims            
    
Synopsis
integer ST_CoordDim(geometry geomA);
    
Examples
SELECT ST_CoordDim('CIRCULARSTRING(1 2 3, 1 3 4, 5 6 7, 8 9 10, 11 12 13)');
SELECT ST_CoordDim(ST_Point(1,2));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_Dimension':
            self.label_17.setText("""ST_Dimension

Description
The inherent dimension of this Geometry object, which must be less than or equal to the coordinate dimension. OGC SPEC s2.1.1.1 - returns 0 for POINT, 1 for LINESTRING, 2 for POLYGON, and the largest dimension of the components of a GEOME TRYCOLLECTION. If unknown (empty geometry) null is returned.            

Synopsis
integer ST_Dimension(geometry g);
            
Examples
SELECT ST_Dimension('GEOMETRYCOLLECTION(LINESTRING(1 1,0 0),POINT(0 0))');""")

        elif self.treeWidget.currentItem().text(0) == 'ST_EndPoint':
            self.label_17.setText("""ST_EndPoint

Description
Returns the last point of a LINESTRING geometry as a POINT or NULL if the input parameter is not a LINESTRING.

Synopsis
boolean ST_EndPoint(geometry g);

Examples
SELECT ST_AsText(ST_EndPoint('LINESTRING(1 1, 2 2, 3 3)'::geometry));                 
SELECT ST_EndPoint('POINT(1 1)'::geometry) IS NULL AS is_null;                  
--3d endpoint
SELECT ST_AsEWKT(ST_EndPoint('LINESTRING(1 1 2, 1 2 3, 0 0 5)'));""")       
            
        elif self.treeWidget.currentItem().text(0) == 'ST_Envelope':
            self.label_17.setText("""ST_Envelope    
            
Description
Returns the float8 minimum bounding box for the supplied geometry, as a geometry. The polygon is defined by the corner points of the bounding box ((MINX, MINY), (MINX, MAXY), (MAXX, MAXY), (MAXX, MINY), (MINX, MINY)). (PostGIS will add
a ZMIN/ZMAX coordinate as well). Degenerate cases (vertical lines, points) will return a geometry of lower dimension than POLYGON, ie. POINT or LINESTRING.            

Synopsis
geometry ST_Envelope(geometry g1);

Examples
SELECT ST_AsText(ST_Envelope('POINT(1 3)'::geometry));
SELECT ST_AsText(ST_Envelope('LINESTRING(0 0, 1 3)'::geometry));
SELECT ST_AsText(ST_Envelope('POLYGON((0 0, 0 1, 1.0000001 1, 1.0000001 0, 0 0))'::geometry));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_BoundingDiagonal':
            self.label_17.setText("""ST_BoundingDiagonal

Description
Returns the diagonal of the supplied geometry's bounding box as linestring. If the input geometry is empty, the diagonal line is also empty, otherwise it is a 2-points linestring with minimum values of each dimension in its start point and maximum values in its end point. The returned linestring geometry always retains SRID and dimensionality (Z and M presence) of the input geometry.
The fits parameter specifies if the best fit is needed. If false, the diagonal of a somewhat larger bounding box can be accepted (is faster to obtain for geometries with a lot of vertices). In any case the bounding box of the returned diagonal line always covers the input geometry.            

Synopsis
geometry ST_BoundingDiagonal(geometry geom, boolean fits=false);

Examples
-- Get the minimum X in a buffer around a point
SELECT ST_X(ST_StartPoint(ST_BoundingDiagonal(ST_Buffer(ST_MakePoint( 0,0),10))));   """)         
            
        elif self.treeWidget.currentItem().text(0) == 'ST_ExteriorRing':
            self.label_17.setText("""ST_ExteriorRing    

Returns a line string representing the exterior ring of the POLYGON geometry. Return NULL if the geometry is not a polygon. Will not work with MULTIPOLYGON            
            
Synopsis
geometry ST_ExteriorRing(geometry a_polygon);            
            
Examples
--If you have a table of polygons
SELECT gid, ST_ExteriorRing(the_geom) AS ering FROM sometable;   

--If you have a table of MULTIPOLYGONs
--and want to return a MULTILINESTRING composed of the exterior rings of each polygon
SELECT gid, ST_Collect(ST_ExteriorRing(the_geom)) AS erings
FROM (SELECT gid, (ST_Dump(the_geom)).geom As the_geom
FROM sometable) As foo GROUP BY gid; """)
            
        elif self.treeWidget.currentItem().text(0) == 'ST_GeometryN':
            self.label_17.setText("""ST_GeometryN

Return the 1-based Nth geometry if the geometry is a GEOMETRYCOLLECTION, (MULTI)POINT, (MULTI)LINESTRING, MULTICURVE or (MULTI)POLYGON, POLYHEDRALSURFACE Otherwise, return NULL.

Synopsis
geometry ST_GeometryN(geometry geomA, integer n);

Standard Examples
--Extracting a subset of points from a 3d multipoint
SELECT n, ST_AsEWKT(ST_GeometryN(the_geom, n)) As geomewkt
FROM (VALUES (ST_GeomFromEWKT('MULTIPOINT(1 2 7, 3 4 7, 5 6 7, 8 9 10)') ),
( ST_GeomFromEWKT('MULTICURVE(CIRCULARSTRING(2.5 2.5,4.5 2.5, 3.5 3.5), (10 11, 12 11))') ))As foo(the_geom)
CROSS JOIN generate_series(1,100) n WHERE n <= ST_NumGeometries(the_geom); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_GeometryType':
            self.label_17.setText("""ST_GeometryType
           
Description
Returns the type of the geometry as a string. EG: 'ST_Linestring', 'ST_Polygon','ST_MultiPolygon' etc. This function differs from GeometryType(geometry) in the case of the string and ST in front that is returned, as well as the fact that it will not indicate whether the geometry is measured.

Synopsis
text ST_GeometryType(geometry g1);

Examples
SELECT ST_GeometryType(ST_GeomFromText('LINESTRING(77.29 29.07,77.42 29.26,77.27 29.31,77.29 29.07)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_InteriorRingN':
            self.label_17.setText("""ST_InteriorRingN
            
Return the Nth interior linestring ring of the polygon geometry. Return NULL if the geometry is not a polygon or the given N is out of range.            

Synopsis
geometry ST_InteriorRingN(geometry a_polygon, integer n);

Examples
SELECT ST_AsText(ST_InteriorRingN(the_geom, 1)) As the_geom
FROM (SELECT ST_BuildArea(
ST_Collect(ST_Buffer(ST_Point(1,2), 20,3),
ST_Buffer(ST_Point(1, 2), 10,3))) As the_geom) as foo """)

        elif self.treeWidget.currentItem().text(0) == 'ST_IsClosed':
            self.label_17.setText("""ST_IsClosed

Returns TRUE if the LINESTRING's start and end points are coincident. For Polyhedral surface is closed (volumetric).

Synopsis
boolean ST_IsClosed(geometry g);

Line String and Point Examples
SELECT ST_IsClosed('LINESTRING(0 0, 1 1)'::geometry);
SELECT ST_IsClosed('POINT(0 0)'::geometry);

Polyhedral Surface Examples
SELECT ST_IsClosed(ST_GeomFromEWKT('POLYHEDRALSURFACE(
((0 0 0, 0 0 1, 0 1 1, 0 1 0, 0 0 0)),((0 0 0, 0 1 0, 1 1 0, 1 0 0, 0 0 0)), 
((0 0 0, 1 0 0, 1 0 1, 0 0 1, 0 0 0)),((1 1 0, 1 1 1, 1 0 1, 1 0 0, 1 1 0)), 
((0 1 0, 0 1 1, 1 1 1, 1 1 0, 0 1 0)), ((0 0 1, 1 0 1, 1 1 1, 0 1 1, 0 0 1)))'));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_IsCollection':
            self.label_17.setText("""ST_IsCollection

Description
Returns TRUE if the geometry type of the argument is either:
• GEOMETRYCOLLECTION
• MULTI{POINT,POLYGON,LINESTRING,CURVE,SURFACE}
• COMPOUNDCURVE

Synopsis
boolean ST_IsCollection(geometry g);

Examples
SELECT ST_IsCollection('LINESTRING(0 0, 1 1)'::geometry);
SELECT ST_IsCollection('MULTIPOINT EMPTY'::geometry);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_IsEmpty':
            self.label_17.setText("""ST_IsEmpty
            
Description
Returns true if this Geometry is an empty geometry. If true, then this Geometry represents an empty geometry collection, polygon, point etc.            

Synopsis
boolean ST_IsEmpty(geometry geomA);

Examples
SELECT ST_IsEmpty(ST_GeomFromText('GEOMETRYCOLLECTION EMPTY'));
SELECT ST_IsEmpty(ST_GeomFromText('POLYGON EMPTY'));
SELECT ST_IsEmpty(ST_GeomFromText('POLYGON((1 2, 3 4, 5 6, 1 2))'));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_IsRing':
            self.label_17.setText("""ST_IsRing
            
Description
Returns TRUE if this LINESTRING is both ST_IsClosed (ST_StartPoint((g)) ~= ST_Endpoint((g))) and ST_IsSimple (does not self intersect).            

Synopsis
boolean ST_IsRing(geometry g);

Examples
SELECT ST_IsRing(the_geom), ST_IsClosed(the_geom), ST_IsSimple(the_geom)
FROM (SELECT 'LINESTRING(0 0, 0 1, 1 1, 1 0, 0 0)'::geometry AS the_geom) AS foo;""")

        elif self.treeWidget.currentItem().text(0) == 'ST_IsSimple':
            self.label_17.setText("""ST_IsSimple
            
Description
Returns true if this Geometry has no anomalous geometric points, such as self intersection or self tangency. For more information on the OGC's definition of geometry simplicity and validity, refer to "Ensuring OpenGIS compliancy of geometries"

Synopsis
boolean ST_IsSimple(geometry geomA);
   
Examples
SELECT ST_IsSimple(ST_GeomFromText('POLYGON((1 2, 3 4, 5 6, 1 2))'));
SELECT ST_IsSimple(ST_GeomFromText('LINESTRING(1 1,2 2,2 3.5,1 3,1 2,2 1)'));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_IsValid':
            self.label_17.setText("""ST_IsValid
            
Description
Test if an ST_Geometry value is well formed. For geometries that are invalid, the PostgreSQL NOTICE will provide details of why it is not valid. For more information on the OGC's definition of geometry simplicity and validity, refer to "Ensuring OpenGIS compliancy of geometries"            

Synopsis
boolean ST_IsValid(geometry g);
boolean ST_IsValid(geometry g, integer flags);

Examples
SELECT ST_IsValid(ST_GeomFromText('LINESTRING(0 0, 1 1)')) As good_line,
ST_IsValid(ST_GeomFromText('POLYGON((0 0, 1 1, 1 2, 1 1, 0 0))')) As bad_poly """)

        elif self.treeWidget.currentItem().text(0) == 'ST_IsValidReason':
            self.label_17.setText("""ST_IsValidReason
            
Description
Returns text stating if a geometry is valid or not an if not valid, a reason why. Useful in combination with ST_IsValid to generate a detailed report of invalid geometries and reasons.            

Synopsis
text ST_IsValidReason(geometry geomA);
text ST_IsValidReason(geometry geomA, integer flags);

Examples
SELECT ST_IsValidReason('LINESTRING(220227 150406,2220227 150407,222020 150410)'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_IsValidDetail':
            self.label_17.setText("""ST_IsValidDetail

Description
Returns a valid_detail row, formed by a boolean (valid) stating if a geometry is valid, a varchar (reason) stating a reason why it is invalid and a geometry (location) pointing out where it is invalid.
Useful to substitute and improve the combination of ST_IsValid and ST_IsValidReason to generate a detailed report of invalid geometries.
The 'flags' argument is a bitfield. It can have the following values:
• 1: Consider self-intersecting rings forming holes as valid. This is also know as "the ESRI flag". Note that this is against the OGC model.

Synopsis
valid_detail ST_IsValidDetail(geometry geom);
valid_detail ST_IsValidDetail(geometry geom, integer flags);

Examples
SELECT * FROM ST_IsValidDetail('LINESTRING(220227 150406,2220227 150407,222020 150410)'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_M':
            self.label_17.setText("""ST_M
            
Return the M coordinate of the point, or NULL if not available. Input must be a point.

Synopsis
float ST_M(geometry a_point);

Examples
SELECT ST_M(ST_GeomFromEWKT('POINT(1 2 3 4)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_NDims':
            self.label_17.setText("""ST_NDims

Description
Returns the coordinate dimension of the geometry. PostGIS supports 2 - (x,y) , 3 - (x,y,z) or 2D with measure - x,y,m, and 4 - 3D with measure space x,y,z,m            

Synopsis
integer ST_NDims(geometry g1);

Examples
SELECT ST_NDims(ST_GeomFromText('POINT(1 1)')) As d2point,
ST_NDims(ST_GeomFromEWKT('POINT(1 1 2)')) As d3point,
ST_NDims(ST_GeomFromEWKT('POINTM(1 1 0.5)')) As d2pointm; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_NPoints':
            self.label_17.setText("""ST_NPoints

Description
Return the number of points in a geometry. Works for all geometries.
Enhanced: 2.0.0 support for Polyhedral surfaces was introduced.

Synopsis
integer ST_NPoints(geometry g1);

Examples
SELECT ST_NPoints(ST_GeomFromText('LINESTRING(77.29 29.07,77.42 29.26,77.27 29.31,77.29 29.07)'));
SELECT ST_NPoints(ST_GeomFromEWKT('LINESTRING(77.29 29.07 1,77.42 29.26 0,77.27 29.31 -1,77.29 29.07 3)')) """)

        elif self.treeWidget.currentItem().text(0) == 'ST_NRings':
            self.label_17.setText("""ST_NRings

If the geometry is a polygon or multi-polygon returns the number of rings. Unlike NumInteriorRings, it counts the outer rings as well.

Synopsis
integer ST_NRings(geometry geomA);

Examples
SELECT ST_NRings(the_geom) As Nrings, ST_NumInteriorRings(the_geom) As ninterrings
FROM (SELECT ST_GeomFromText('POLYGON((1 2, 3 4, 5 6, 1 2))') As the_geom) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_NumGeometries':
            self.label_17.setText("""ST_NumGeometries
            
Description
Returns the number of Geometries. If geometry is a GEOMETRYCOLLECTION (or MULTI*) return the number of geometries, for single geometries will return 1, otherwise return NULL.
Enhanced: 2.0.0 support for Polyhedral surfaces, Triangles and TIN was introduced.            

Synopsis
integer ST_NumGeometries(geometry geom);

Examples
SELECT ST_NumGeometries(ST_GeomFromText('LINESTRING(77.29 29.07,77.42 29.26,77.27 29.31,77.29 29.07)'));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_NumInteriorRings':
            self.label_17.setText("""ST_NumInteriorRings
            
Return the number of interior rings of a polygon geometry. Return NULL if the geometry is not a polygon.            

Synopsis
integer ST_NumInteriorRings(geometry a_polygon);
            
 Examples
--If you have a regular polygon
SELECT gid, field1, field2, ST_NumInteriorRings(the_geom) AS numholes FROM sometable;      

--If you have multipolygons
--And you want to know the total number of interior rings in the MULTIPOLYGON
SELECT gid, field1, field2, SUM(ST_NumInteriorRings(the_geom)) AS numholes
FROM (SELECT gid, field1, field2, (ST_Dump(the_geom)).geom As the_geom
FROM sometable) As foo GROUP BY gid, field1,field2;  """)
    
        elif self.treeWidget.currentItem().text(0) == 'ST_NumPatches':
            self.label_17.setText("""ST_NumPatches
            
Description
Return the number of faces on a Polyhedral Surface. Will return null for non-polyhedral geometries. This is an alias for ST_NumGeometries to support MM naming. Faster to use ST_NumGeometries if you don't care about MM convention.            

Synopsis
integer ST_NumPatches(geometry g1);
  
Examples
SELECT ST_NumPatches(ST_GeomFromEWKT('POLYHEDRALSURFACE( ((0 0 0, 0 0 1, 0 1 1, 0 1 0, 0 0 0)),
((0 0 0, 0 1 0, 1 1 0, 1 0 0, 0 0 0)), ((0 0 0, 1 0 0, 1 0 1, 0 0 1, 0 0 0)), 
((1 1 0, 1 1 1, 1 0 1, 1 0 0, 1 1 0)), ((0 1 0, 0 1 1, 1 1 1, 1 1 0, 0 1 0)), 
((0 0 1, 1 0 1, 1 1 1, 0 1 1, 0 0 1)) )'));  """)
            
        elif self.treeWidget.currentItem().text(0) == 'ST_NumPoints':
            self.label_17.setText("""ST_NumPoints    
            
Description
Return the number of points in an ST_LineString or ST_CircularString value. Prior to 1.4 only works with Linestrings as the specs state. From 1.4 forward this is an alias for ST_NPoints which returns number of vertexes for not just line strings. Consider using ST_NPoints instead which is multi-purpose and works with many geometry types.            

Synopsis
integer ST_NumPoints(geometry g1);
            
Examples
SELECT ST_NumPoints(ST_GeomFromText('LINESTRING(77.29 29.07,77.42 29.26,77.27 29.31,77.29 29.07)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_PatchN':
            self.label_17.setText("""ST_PatchN 
            
Description
Return the 1-based Nth geometry (face) if the geometry is a POLYHEDRALSURFACE, POLYHEDRALSURFACEM. Otherwise, return NULL. This returns the same answer as ST_GeometryN for Polyhedral Surfaces. Using ST_GemoetryN is faster.            
       
Synopsis
geometry ST_PatchN(geometry geomA, integer n);
       
Examples
--Extract the 2nd face of the polyhedral surface
SELECT ST_AsEWKT(ST_PatchN(geom, 2)) As geomewkt FROM (
VALUES (ST_GeomFromEWKT('POLYHEDRALSURFACE( ((0 0 0, 0 0 1, 0 1 1, 0 1 0, 0 0 0)),
((0 0 0, 0 1 0, 1 1 0, 1 0 0, 0 0 0)), ((0 0 0, 1 0 0, 1 0 1, 0 0 1, 0 0 0)),
((1 1 0, 1 1 1, 1 0 1, 1 0 0, 1 1 0)), ((0 1 0, 0 1 1, 1 1 1, 1 1 0, 0 1 0)), 
((0 0 1, 1 0 1, 1 1 1, 0 1 1, 0 0 1)) )')) ) As foo(geom); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_PointN':
            self.label_17.setText("""ST_PointN
            
Description
Return the Nth point in a single linestring or circular linestring in the geometry. Negative values are counted backwards from the end of the LineString, so that -1 is the last point. Returns NULL if there is no linestring in the geometry.            
            
Synopsis
geometry ST_PointN(geometry a_linestring, integer n);            
            
Examples
-- Extract all POINTs from a LINESTRING
SELECT ST_AsText(ST_PointN(column1,
generate_series(1, ST_NPoints(column1))))
FROM ( VALUES ('LINESTRING(0 0, 1 1, 2 2)'::geometry) ) AS foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Points':
            self.label_17.setText("""ST_Points

Description
Returns a MultiPoint containing all of the coordinates of a geometry. Does not remove points that are duplicated in the input geometry, including start and end points of ring geometries. (If this behavior is undesired, duplicates may be removed using ST_RemoveRepeatedPoints). M and Z ordinates will be preserved if present.

Synopsis
geometry ST_Points( geometry geom );

Examples
SELECT ST_AsText(ST_Points('POLYGON Z ((30 10 4,10 30 5,40 40 6, 30 10))')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_SRID':
            self.label_17.setText("""ST_SRID
            
Returns the spatial reference identifier for the ST_Geometry as defined in spatial_ref_sys table.

Synopsis
integer ST_SRID(geometry g1);

Examples
SELECT ST_SRID(ST_GeomFromText('POINT(-71.1043 42.315)',4326)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_StartPoint':
            self.label_17.setText("""ST_StartPoint

Description
Returns the first point of a LINESTRING or CIRCULARLINESTRING geometry as a POINT or NULL if the input parameter is not a LINESTRING or CIRCULARLINESTRING.

Synopsis
geometry ST_StartPoint(geometry geomA);

Examples
SELECT ST_AsText(ST_StartPoint('LINESTRING(0 1, 0 2)'::geometry));
SELECT ST_StartPoint('POINT(0 1)'::geometry) IS NULL AS is_null;
SELECT ST_AsEWKT(ST_StartPoint('LINESTRING(0 1 1, 0 2 2)'::geometry));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_Summary':
            self.label_17.setText("""ST_Summary
            
Description
Returns a text summary of the contents of the geometry.
Flags shown square brackets after the geometry type have the following meaning:
• M: has M ordinate
• Z: has Z ordinate
• B: has a cached bounding box
• G: is geodetic (geography)
• S: has spatial reference system

Synopsis
text ST_Summary(geometry g);
text ST_Summary(geography g);

SELECT ST_Summary(ST_GeomFromText('LINESTRING(0 0, 1 1)')) as geom,
ST_Summary(ST_GeogFromText('POLYGON((0 0, 1 1, 1 2, 1 1, 0 0))')) geog; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_X':
            self.label_17.setText("""ST_X
            
Return the X coordinate of the point, or NULL if not available. Input must be a point.

Synopsis
float ST_X(geometry a_point);

Examples 
SELECT gid, ST_X(geom), ST_Y(geom) FROM tabel_name
SELECT ST_X(ST_GeomFromEWKT('POINT(1 2 3 4)'));
SELECT ST_Y(ST_Centroid(ST_GeomFromEWKT('LINESTRING(1 2 3 4, 1 1 1 1)')));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_XMax':
            self.label_17.setText("""ST_XMax
            
Returns X maxima of a bounding box 2d or 3d or a geometry.

Synopsis
float ST_XMax(box3d aGeomorBox2DorBox3D);

Examples
SELECT ST_XMax('BOX3D(1 2 3, 4 5 6)');
SELECT ST_XMax(ST_GeomFromText('LINESTRING(1 3 4, 5 6 7)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_XMin':
            self.label_17.setText("""ST_XMin

Returns X minima of a bounding box 2d or 3d or a geometry.

Synopsis
float ST_XMin(box3d aGeomorBox2DorBox3D);

Examples
SELECT ST_XMin('BOX3D(1 2 3, 4 5 6)');
SELECT ST_XMin(CAST('BOX(-3 2, 3 4)' As box2d)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Y':
            self.label_17.setText("""ST_Y

Return the Y coordinate of the point, or NULL if not available. Input must be a point.

Synopsis
float ST_Y(geometry a_point);

Examples
SELECT gid, ST_X(geom), ST_Y(geom) FROM tabel_name
SELECT ST_Y(ST_GeomFromEWKT('POINT(1 2 3 4)'));
SELECT ST_Y(ST_Centroid(ST_GeomFromEWKT('LINESTRING(1 2 3 4, 1 1 1 1)')));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_YMax':
            self.label_17.setText("""ST_YMax
            
Returns Y maxima of a bounding box 2d or 3d or a geometry.

Synopsis
float ST_YMax(box3d aGeomorBox2DorBox3D);

Examples
SELECT ST_YMax('BOX3D(1 2 3, 4 5 6)');
SELECT ST_YMax(ST_GeomFromText('LINESTRING(1 3 4, 5 6 7)'));
SELECT ST_YMax(CAST('BOX(-3 2, 3 4)' As box2d));""")

        elif self.treeWidget.currentItem().text(0) == 'ST_YMin':
            self.label_17.setText("""ST_YMin
            
Returns Y minima of a bounding box 2d or 3d or a geometry.

Synopsis
float ST_YMin(box3d aGeomorBox2DorBox3D);

Examples
SELECT ST_YMin('BOX3D(1 2 3, 4 5 6)');
SELECT ST_YMin(ST_GeomFromText('LINESTRING(1 3 4, 5 6 7)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Z':
            self.label_17.setText("""ST_Z
            
Return the Z coordinate of the point, or NULL if not available. Input must be a point.

Synopsis
float ST_Z(geometry a_point);

Examples
SELECT ST_Z(ST_GeomFromEWKT('POINT(1 2 3 4)'));  """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ZMax':
            self.label_17.setText("""ST_ZMax
            
Returns Z minima of a bounding box 2d or 3d or a geometry.

Synopsis
float ST_ZMax(box3d aGeomorBox2DorBox3D);

Examples
SELECT ST_ZMax('BOX3D(1 2 3, 4 5 6)');
SELECT ST_ZMax(ST_GeomFromEWKT('LINESTRING(1 3 4, 5 6 7)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Zmflag':
            self.label_17.setText("""ST_Zmflag

Returns ZM (dimension semantic) flag of the geometries as a small int. Values are: 0=2d, 1=3dm, 2=3dz, 3=4d.

Synopsis
smallint ST_Zmflag(geometry geomA);

Examples
SELECT ST_Zmflag(ST_GeomFromEWKT('LINESTRING(1 2, 3 4)'));
SELECT ST_Zmflag(ST_GeomFromEWKT('LINESTRINGM(1 2 3, 3 4 3)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ZMin':
            self.label_17.setText("""ST_ZMin
            
Returns Z minima of a bounding box 2d or 3d or a geometry.

Synopsis
float ST_ZMin(box3d aGeomorBox2DorBox3D);

Examples
SELECT ST_ZMin('BOX3D(1 2 3, 4 5 6)');
SELECT ST_ZMin(ST_GeomFromEWKT('LINESTRING(1 3 4, 5 6 7)')); """)

#8.6 Geometry Editors

        elif self.treeWidget.currentItem().text(0) == 'ST_AddPoint':
            self.label_17.setText("""ST_AddPoint
            
Description
Adds a point to a LineString before point <position> (0-based index). Third parameter can be omitted or set to -1 for appending.

Synopsis
geometry ST_AddPoint(geometry linestring, geometry point);
geometry ST_AddPoint(geometry linestring, geometry point, integer position);

Examples
UPDATE sometable
SET the_geom = ST_AddPoint(the_geom, ST_StartPoint(the_geom))
FROM sometable
WHERE ST_IsClosed(the_geom) = false;  """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Affine':
            self.label_17.setText("""ST_Affine

Description
Applies a 3d affine transformation to the geometry to do things like translate, rotate, scale in one step.

Synopsis
geometry ST_Affine(geometry geomA, float a, float b, float c, float d, float e, float f, float g, float h, float i, float xoff, float yoff, float zoff);
geometry ST_Affine(geometry geomA, float a, float b, float d, float e, float xoff, float yoff);

Examples
--Rotate a 3d line 180 degrees about the z axis. Note this is long-hand for doing ST_Rotate();
SELECT ST_AsEWKT(ST_Affine(the_geom, cos(pi()), -sin(pi()), 0, sin(pi()), cos(pi()), 0, 0, 0, 1, 0, 0, 0)) As using_affine,
ST_AsEWKT(ST_Rotate(the_geom, pi())) As using_rotate
FROM (SELECT ST_GeomFromEWKT('LINESTRING(1 2 3, 1 4 3)') As the_geom) As foo; """)     

        elif self.treeWidget.currentItem().text(0) == 'ST_Force2D':
            self.label_17.setText("""ST_Force2D
            
Description
Forces the geometries into a "2-dimensional mode" so that all output representations will only have the X and Y coordinates. This is useful for force OGC-compliant output (since OGC only specifies 2-D geometries).         

Synopsis
geometry ST_Force2D(geometry geomA);
            
Examples
SELECT ST_AsEWKT(ST_Force2D(ST_GeomFromEWKT('CIRCULARSTRING(1 1 2, 2 3 2, 4 5 2, 6 7 2, 5 6 2)')));   
SELECT ST_AsEWKT(ST_Force2D('POLYGON((0 0 2,0 5 2,5 0 2,0 0 2),(1 1 2,3 1 2,1 3 2,1 1 2))')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Force3D':
            self.label_17.setText("""ST_Force3D
            
Description
Forces the geometries into XYZ mode. This is an alias for ST_Force_3DZ. If a geometry has no Z component, then a 0 Z coordinate is tacked on.

Synopsis
geometry ST_Force3D(geometry geomA);

Examples
--Nothing happens to an already 3D geometry
SELECT ST_AsEWKT(ST_Force3D(ST_GeomFromEWKT('CIRCULARSTRING(1 1 2, 2 3 2, 4 5 2, 6 7 2, 5 6 2)')));

SELECT ST_AsEWKT(ST_Force3D('POLYGON((0 0,0 5,5 0,0 0),(1 1,3 1,1 3,1 1))')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Force3DZ':
            self.label_17.setText("""ST_Force3DZ
            
Description
Forces the geometries into XYZ mode. This is a synonym for ST_Force3DZ. If a geometry has no Z component, then a 0 Z coordinate is tacked on.

Synopsis
geometry ST_Force3DZ(geometry geomA);

--Nothing happens to an already 3D geometry
SELECT ST_AsEWKT(ST_Force3DZ(ST_GeomFromEWKT('CIRCULARSTRING(1 1 2, 2 3 2, 4 5 2, 6 7 2, 5 6 2)')));

SELECT ST_AsEWKT(ST_Force3DZ('POLYGON((0 0,0 5,5 0,0 0),(1 1,3 1,1 3,1 1))')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Force3DM':
            self.label_17.setText("""ST_Force3DM

Description
Forces the geometries into XYM mode. If a geometry has no M component, then a 0 M coordinate is tacked on. If it has a Z component, then Z is removed

Synopsis
geometry ST_Force3DM(geometry geomA);

Examples
--Nothing happens to an already 3D geometry
SELECT ST_AsEWKT(ST_Force3DM(ST_GeomFromEWKT('CIRCULARSTRING(1 1 2, 2 3 2, 4 5 2, 6 7 2, 5 6 2)')));

SELECT ST_AsEWKT(ST_Force3DM('POLYGON((0 0 1,0 5 1,5 0 1,0 0 1),(1 1 1,3 1 1,1 3 1,1 1 1))')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Force4D':
            self.label_17.setText("""ST_Force4D
            
Description
Forces the geometries into XYZM mode. 0 is tacked on for missing Z and M dimensions.

Synopsis
geometry ST_Force4D(geometry geomA);

Examples
--Nothing happens to an already 3D geometry
SELECT ST_AsEWKT(ST_Force4D(ST_GeomFromEWKT('CIRCULARSTRING(1 1 2, 2 3 2, 4 5 2, 6 7 2, 5 6 2)')));

SELECT ST_AsEWKT(ST_Force4D('MULTILINESTRINGM((0 0 1,0 5 2,5 0 3,0 0 4),(1 1 1,3 1 1,1 3 1,1 1 1))')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ForceCollection':
            self.label_17.setText("""ST_ForceCollection
            
Description
Converts the geometry into a GEOMETRYCOLLECTION. This is useful for simplifying the WKB representation. Enhanced: 2.0.0 support for Polyhedral surfaces was introduced.

Synopsis
geometry ST_ForceCollection(geometry geomA);

Examples
SELECT ST_AsEWKT(ST_ForceCollection('POLYGON((0 0 1,0 5 1,5 0 1,0 0 1),(1 1 1,3 1 1,1 3 1,1 1 1))')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ForceSFS':
            self.label_17.setText("""ST_ForceSFS
            
Force the geometries to use SFS 1.1 geometry types only.

Synopsis
geometry ST_ForceSFS(geometry geomA);
geometry ST_ForceSFS(geometry geomA, text version); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ForceRHR':
            self.label_17.setText("""ST_ForceRHR
            
Description
Forces the orientation of the vertices in a polygon to follow the Right-Hand-Rule. In GIS terminology, this means that the area that is bounded by the polygon is to the right of the boundary. In particular, the exterior ring is orientated in a clockwise direction and the interior rings in a counter-clockwise direction.

Synopsis
geometry ST_ForceRHR(geometry g);

Examples
SELECT ST_AsEWKT(ST_ForceRHR('POLYGON((0 0 2, 5 0 2, 0 5 2, 0 0 2),(1 1 2, 1 3 2, 3 1 2, 1 1 2))')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ForceCurve':
            self.label_17.setText("""ST_ForceCurve
            
Description
Turns a geometry into its curved representation, if applicable: lines become compoundcurves, multilines become multicurves polygons become curvepolygons multipolygons become multisurfaces. If the geometry input is already a curved representation returns back same as input.

Synopsis
geometry ST_ForceCurve(geometry g);

Examples
SELECT ST_AsText(ST_ForceCurve('POLYGON((0 0 2, 5 0 2, 0 5 2, 0 0 2),(1 1 2, 1 3 2, 3 1 2, 1 1 2))'::geometry)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_LineMerge':
            self.label_17.setText("""ST_LineMerge
            
Returns a (set of) LineString(s) formed by sewing together the constituent line work of a MULTILINESTRING.

Synopsis
geometry ST_LineMerge(geometry amultilinestring);

Examples
SELECT ST_AsText(ST_LineMerge(
ST_GeomFromText('MULTILINESTRING((-29 -27,-30 -29.7,-36 -31,-45 -33),(-45 -33,-46 -32))')));  """)

        elif self.treeWidget.currentItem().text(0) == 'ST_CollectionExtract':
            self.label_17.setText("""ST_CollectionExtract

Description
Given a (multi)geometry, returns a (multi)geometry consisting only of elements of the specified type. Sub-geometries that are not the specified type are ignored. If there are no sub-geometries of the right type, an EMPTY geometry will be returned. Only points, lines and polygons are supported. Type numbers are 1 == POINT, 2 == LINESTRING, 3 == POLYGON.

Synopsis
geometry ST_CollectionExtract(geometry collection, integer type);

-- Constants: 1 == POINT, 2 == LINESTRING, 3 == POLYGON
SELECT ST_AsText(ST_CollectionExtract(ST_GeomFromText( 'GEOMETRYCOLLECTION( GEOMETRYCOLLECTION(POINT(0 0)))'),1));

SELECT ST_AsText(ST_CollectionExtract(ST_GeomFromText('GEOMETRYCOLLECTION( GEOMETRYCOLLECTION(LINESTRING(0 0, 1 1)),LINESTRING(2 2, 3 3))'),2)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_CollectionHomogenize':
            self.label_17.setText("""ST_CollectionHomogenize
            
Description
Given a geometry collection, returns the "simplest" representation of the contents. Singletons will be returned as singletons. Collections that are homogeneous will be returned as the appropriate multi-type.            

Synopsis
geometry ST_CollectionHomogenize(geometry collection);

Examples
SELECT ST_AsText(ST_CollectionHomogenize('GEOMETRYCOLLECTION(POINT(0 0))'));
SELECT ST_AsText(ST_CollectionHomogenize('GEOMETRYCOLLECTION(POINT(0 0),POINT(1 1))')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Multi':
            self.label_17.setText("""ST_Multi

Returns the geometry as a MULTI* geometry. If the geometry is already a MULTI*, it is returned unchanged.

Synopsis
geometry ST_Multi(geometry g1);

Examples
SELECT ST_AsText(ST_Multi(ST_GeomFromText('POLYGON((743238 2967416,743238 2967450,743265 2967450,743265.625 2967416,743238 2967416))'))); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Normalize':
            self.label_17.setText("""ST_Normalize
            
Description
Returns the geometry in its normalized/canonical form. May reorder vertices in polygon rings, rings in a polygon, elements in a multi-geometry complex. Mostly only useful for testing purposes (comparing expected and obtained results).            

Synopsis
geometry ST_Normalize(geometry geom);

Examples
GEOMETRYCOLLECTION(POLYGON((0 0,0 10,10 10,10 0,0 0),(6 6,8 6,8 8,6 8,6 6),(2 2,4 2,4 4,2 4,2 2)),MULTILINESTRING((2 2,3 3),(0 0,1 1)),POINT(2 3)) """)

        elif self.treeWidget.currentItem().text(0) == 'ST_RemovePoint':
            self.label_17.setText("""ST_RemovePoint

Remove a point from a linestring, given its 0-based index. Useful for turning a closed ring into an open line string.

Synopsis
geometry ST_RemovePoint(geometry linestring, integer offset);

Examples
--guarantee no LINESTRINGS are closed
--by removing the end point. The below assumes the_geom is of type LINESTRING
UPDATE sometable
SET the_geom = ST_RemovePoint(the_geom, ST_NPoints(the_geom) - 1)
FROM sometable
WHERE ST_IsClosed(the_geom) = true; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Reverse':
            self.label_17.setText("""ST_Reverse
            
Can be used on any geometry and reverses the order of the vertexes.

Synopsis
geometry ST_Reverse(geometry g1);

Examples
SELECT ST_AsText(the_geom) as line, ST_AsText(ST_Reverse(the_geom)) As reverseline
FROM (SELECT ST_MakeLine(ST_MakePoint(1,2), ST_MakePoint(1,10)) As the_geom) as foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Rotate':
            self.label_17.setText("""ST_Rotate
            
Description
Rotates geometry rotRadians counter-clockwise about the origin. The rotation origin can be specified either as a POINT geometry, or as x and y coordinates. If the origin is not specified, the geometry is rotated about POINT(0 0).            

Synopsis
geometry ST_Rotate(geometry geomA, float rotRadians);
geometry ST_Rotate(geometry geomA, float rotRadians, float x0, float y0);
geometry ST_Rotate(geometry geomA, float rotRadians, geometry pointOrigin);

Examples
--Rotate 180 degrees
SELECT ST_AsEWKT(ST_Rotate('LINESTRING (50 160, 50 50, 100 50)', pi()));

--Rotate 30 degrees counter-clockwise at x=50, y=160
SELECT ST_AsEWKT(ST_Rotate('LINESTRING (50 160, 50 50, 100 50)', pi()/6, 50, 160)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_RotateX':
            self.label_17.setText("""ST_RotateX
            
Rotate a geometry geomA - rotRadians about the X axis.

Synopsis
geometry ST_RotateX(geometry geomA, float rotRadians);

Examples
--Rotate a line 90 degrees along x-axis
SELECT ST_AsEWKT(ST_RotateX(ST_GeomFromEWKT('LINESTRING(1 2 3, 1 1 1)'), pi()/2)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_RotateY':
            self.label_17.setText("""ST_RotateY

Rotate a geometry geomA - rotRadians about the y axis.

Synopsis
geometry ST_RotateY(geometry geomA, float rotRadians);

Examples
--Rotate a line 90 degrees along y-axis
SELECT ST_AsEWKT(ST_RotateY(ST_GeomFromEWKT('LINESTRING(1 2 3, 1 1 1)'), pi()/2)); """)


        elif self.treeWidget.currentItem().text(0) == 'ST_RotateZ':
            self.label_17.setText("""ST_RotateZ    

Rotate a geometry geomA - rotRadians about the Z axis.

Synopsis
geometry ST_RotateZ(geometry geomA, float rotRadians);

Examples
--Rotate a line 90 degrees along z-axis
SELECT ST_AsEWKT(ST_RotateZ(ST_GeomFromEWKT('LINESTRING(1 2 3, 1 1 1)'), pi()/2)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Scale':
            self.label_17.setText("""ST_Scale

Description
Scales the geometry to a new size by multiplying the ordinates with the corresponding factor parameters. The version taking a geometry as the factor parameter allows passing a 2d, 3dm, 3dz or 4d point to set scaling factor for all supported dimensions. Missing dimensions in the factor point are equivalent to no scaling the corresponding dimension.

Synopsis
geometry ST_Scale(geometry geomA, float XFactor, float YFactor, float ZFactor);
geometry ST_Scale(geometry geomA, float XFactor, float YFactor);
geometry ST_Scale(geometry geom, geometry factor);

Examples
--Version 1: scale X, Y, Z
SELECT ST_AsEWKT(ST_Scale(ST_GeomFromEWKT('LINESTRING(1 2 3, 1 1 1)'), 0.5, 0.75, 0.8));

--Version 2: Scale X Y
SELECT ST_AsEWKT(ST_Scale(ST_GeomFromEWKT('LINESTRING(1 2 3, 1 1 1)'), 0.5, 0.75));

--Version 3: Scale X Y Z M
SELECT ST_AsEWKT(ST_Scale(ST_GeomFromEWKT('LINESTRING(1 2 3 4, 1 1 1 1)'), ST_MakePoint(0.5, 0.75, 2, -1))); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Segmentize':
            self.label_17.setText("""ST_Segmentize
            
Description
Returns a modified geometry having no segment longer than the given max_segment_length. Distance computation is performed in 2d only. For geometry, length units are in units of spatial reference. For geography, units are in meters.            

Synopsis
geometry ST_Segmentize(geometry geom, float max_segment_length);
geography ST_Segmentize(geography geog, float max_segment_length);

Examples
SELECT ST_AsText(ST_Segmentize(
ST_GeomFromText('MULTILINESTRING((-29 -27,-30 -29.7,-36 -31,-45 -33),(-45 -33,-46 -32))'),5)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_SetPoint':
            self.label_17.setText("""ST_SetPoint
            
Description
Replace point N of linestring with given point. Index is 0-based.Negative index are counted backwards, so that -1 is last point. This is especially useful in triggers when trying to maintain relationship of joints when one vertex moves.

Synopsis
geometry ST_SetPoint(geometry linestring, integer zerobasedposition, geometry point);

Examples
--Change first point in line string from -1 3 to -1 1
SELECT ST_AsText(ST_SetPoint('LINESTRING(-1 2,-1 3)', 0, 'POINT(-1 1)'));

SELECT ST_AsText(ST_SetPoint(g, -3, p))
FROM ST_GEomFromText('LINESTRING(0 0, 1 1, 2 2, 3 3, 4 4)') AS g, ST_PointN(g,1) as p; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_SetSRID':
            self.label_17.setText("""ST_SetSRID

Sets the SRID on a geometry to a particular integer value. Useful in constructing bounding boxes for queries.

Synopsis
geometry ST_SetSRID(geometry geom, integer srid);

Examples
-- Mark a point as WGS 84 long lat --
SELECT ST_SetSRID(ST_Point(-123.365556, 48.428611),4326) As wgs84long_lat;

-- the ewkt representation (wrap with ST_AsEWKT) -
SRID=4326;POINT(-123.365556 48.428611)

-- Mark a point as WGS 84 long lat and then transform to web mercator (Spherical Mercator) --
SELECT ST_Transform(ST_SetSRID(ST_Point(-123.365556, 48.428611),4326),3785) As spere_merc;

-- the ewkt representation (wrap with ST_AsEWKT) -
SRID=3785;POINT(-13732990.8753491 6178458.96425423) """)

        elif self.treeWidget.currentItem().text(0) == 'ST_SnapToGrid':
            self.label_17.setText("""ST_SnapToGrid

Description
Variant 1,2,3: Snap all points of the input geometry to the grid defined by its origin and cell size. Remove consecutive points falling on the same cell, eventually returning NULL if output points are not enough to define a geometry of the given type. Collapsed geometries in a collection are stripped from it. Useful for reducing precision.

Synopsis
geometry ST_SnapToGrid(geometry geomA, float originX, float originY, float sizeX, float sizeY);
geometry ST_SnapToGrid(geometry geomA, float sizeX, float sizeY);
geometry ST_SnapToGrid(geometry geomA, float size);
geometry ST_SnapToGrid(geometry geomA, geometry pointOrigin, float sizeX, float sizeY, float sizeZ, float sizeM);

Examples
--Snap your geometries to a precision grid of 10^-3
UPDATE mytable
SET the_geom = ST_SnapToGrid(the_geom, 0.001);

SELECT ST_AsText(ST_SnapToGrid(ST_GeomFromText('LINESTRING(1.1115678 2.123, 4.111111 3.2374897, 4.11112 3.23748667)'),0.001)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Snap':
            self.label_17.setText("""ST_Snap

Description
Snaps the vertices and segments of a geometry another Geometry's vertices. A snap distance tolerance is used to control where snapping is performed. Snapping one geometry to another can improve robustness for overlay operations by eliminating nearly-coincident edges (which cause problems during noding and intersection calculation). Too much snapping can result in invalid topology being created, so the number and location of snapped vertices is decided using heuristics to determine when it is safe to snap. This can result in some potential snaps being omitted, however.

Synopsis
geometry ST_Snap(geometry input, geometry reference, float tolerance);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_Transform':
            self.label_17.setText("""ST_Transform

Description
Returns a new geometry with its coordinates transformed to a different spatial reference system. The destination spatial reference to_srid may be identified by a valid SRID integer parameter (i.e. it must exist in the spatial_ref_sys table). Alternatively, a spatial reference defined as a PROJ.4 string can be used for to_proj and/or from_proj, however these methods are not optimized. If the destination spatial reference system is expressed with a PROJ.4 string instead of an SRID, the SRID of the output geometry will be set to zero. With the exception of functions with from_proj, input geometries must have a defined SRID.
ST_Transform is often confused with ST_SetSRID(). ST_Transform actually changes the coordinates of a geometry from one spatial reference system to another, while ST_SetSRID() simply changes the SRID identifier of the geometry.

Synopsis
geometry ST_Transform(geometry g1, integer srid);
geometry ST_Transform(geometry geom, text to_proj);
geometry ST_Transform(geometry geom, text from_proj, text to_proj);
geometry ST_Transform(geometry geom, text from_proj, integer to_srid);

Examples
Change Massachusetts state plane US feet geometry to WGS 84 long lat

SELECT ST_AsText(ST_Transform(ST_GeomFromText('POLYGON((743238 2967416,743238 2967450, 743265 2967450,743265.625 2967416,743238 2967416))',2249),4326)) As wgs_geom;

--3D Circular String example
SELECT ST_AsEWKT(ST_Transform(ST_GeomFromEWKT('SRID=2249;CIRCULARSTRING( 743238 2967416 1,743238 2967450 2,743265 2967450 3,743265.625 2967416 3,743238 2967416 4)'),4326)); 
""")
        elif self.treeWidget.currentItem().text(0) == 'ST_Translate':
            self.label_17.setText("""ST_Translate
        
Description
Returns a new geometry whose coordinates are translated delta x,delta y,delta z units. Units are based on the units defined in spatial reference (SRID) for this geometry.

Synopsis
geometry ST_Translate(geometry g1, float deltax, float deltay);
geometry ST_Translate(geometry g1, float deltax, float deltay, float deltaz);

Examples
--Move a point 1 degree longitude
SELECT ST_AsText(ST_Translate(ST_GeomFromText('POINT(-71.01 42.37)',4326),1,0)) As  wgs_transgeomtxt;

Move a linestring 1 degree longitude and 1/2 degree latitude
SELECT ST_AsText(ST_Translate(ST_GeomFromText('LINESTRING(-71.01 42.37,-71.11 42.38)',4326) ,1,0.5)) As wgs_transgeomtxt; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_TransScale':
            self.label_17.setText("""ST_TransScale

Translates the geometry using the deltaX and deltaY args, then scales it using the XFactor, YFactor args, working in 2D only.

Synopsis
geometry ST_TransScale(geometry geomA, float deltaX, float deltaY, float XFactor, float YFactor);

Examples
SELECT ST_AsEWKT(ST_TransScale(ST_GeomFromEWKT('LINESTRING(1 2 3, 1 1 1)'), 0.5, 1, 1, 2));

--Buffer a point to get an approximation of a circle, convert to curve and then translate 1,2 and scale it 3,4
SELECT ST_AsText(ST_Transscale(ST_LineToCurve(ST_Buffer('POINT(234 567)', 3)),1,2,3,4)); """)

#8.7 Geometry Outputs
        elif self.treeWidget.currentItem().text(0) == 'ST_AsBinary':
            self.label_17.setText("""ST_AsBinary
            
Description
Returns the Well-Known Binary representation of the geometry. There are 2 variants of the function. The first variant takes no endian encoding parameter and defaults to server machine endian. The second variant takes a second argument denoting the encoding - using little-endian ('NDR') or big-endian ('XDR') encoding. This is useful in binary cursors to pull data out of the database without converting it to a string representation.

Synopsis
bytea ST_AsBinary(geometry g1);
bytea ST_AsBinary(geometry g1, text NDR_or_XDR);
bytea ST_AsBinary(geography g1);
bytea ST_AsBinary(geography g1, text NDR_or_XDR);

Examples
SELECT ST_AsBinary(ST_GeomFromText('POLYGON((0 0,0 1,1 1,1 0,0 0))',4326));
SELECT ST_AsBinary(ST_GeomFromText('POLYGON((0 0,0 1,1 1,1 0,0 0))',4326), 'XDR'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsEncodedPolyline':
            self.label_17.setText("""ST_AsEncodedPolyline

Returns the geometry as an Encoded Polyline. This is a format very useful if you are using google maps

Synopsis
text ST_AsEncodedPolyline(geometry geom, integer precision=5);

Examples
SELECT ST_AsEncodedPolyline(GeomFromEWKT('SRID=4326;LINESTRING(-120.2 38.5,-120.95 40.7,-126.453 43.252)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsEWKB':
            self.label_17.setText("""ST_AsEWKB

Description
Returns the Well-Known Binary representation of the geometry with SRID metadata. There are 2 variants of the function. The first variant takes no endian encoding parameter and defaults to little endian. The second variant takes a second argument denoting the encoding - using little-endian ('NDR') or big-endian ('XDR') encoding. This is useful in binary cursors to pull data out of the database without converting it to a string representation.

Synopsis
bytea ST_AsEWKB(geometry g1);
bytea ST_AsEWKB(geometry g1, text NDR_or_XDR);

Examples
SELECT ST_AsEWKB(ST_GeomFromText('POLYGON((0 0,0 1,1 1,1 0,0 0))',4326)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsEWKT':
            self.label_17.setText("""ST_AsEWKT
            
Returns the Well-Known Text representation of the geometry prefixed with the SRID.

Synopsis
text ST_AsEWKT(geometry g1);
text ST_AsEWKT(geography g1);

Examples
SELECT ST_AsEWKT('0103000020E61000000100000005000000000000
000000000000000000000000000000000000000000000000000000
F03F000000000000F03F000000000000F03F000000000000F03
F000000000000000000000000000000000000000000000000'::geometry); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsGeoJSON':
            self.label_17.setText("""ST_AsGeoJSON   

Description
Return the geometry as a Geometry Javascript Object Notation (GeoJSON) element. (Cf GeoJSON specifications 1.0). 2D and 3D Geometries are both supported. GeoJSON only support SFS 1.1 geometry type (no curve support for example).
The gj_version parameter is the major version of the GeoJSON spec. If specified, must be 1. This represents the spec version of GeoJSON. The third argument may be used to reduce the maximum number of decimal places used in output (defaults to 15). The last 'options' argument could be used to add Bbox or Crs in GeoJSON output:
• 0: means no option (default value)
• 1: GeoJSON Bbox
• 2: GeoJSON Short CRS (e.g EPSG:4326)
• 4: GeoJSON Long CRS (e.g urn:ogc:def:crs:EPSG::4326)

Synopsis
text ST_AsGeoJSON(geometry geom, integer maxdecimaldigits=15, integer options=0);
text ST_AsGeoJSON(geography geog, integer maxdecimaldigits=15, integer options=0);
text ST_AsGeoJSON(integer gj_version, geometry geom, integer maxdecimaldigits=15, integer options=0);
text ST_AsGeoJSON(integer gj_version, geography geog, integer maxdecimaldigits=15, integer options=0);

Examples
GeoJSON format is generally more efficient than other formats for use in ajax mapping. One popular javascript client that supports this is Open Layers. Example of its use is OpenLayers GeoJSON Example
SELECT ST_AsGeoJSON(the_geom) from fe_edges limit 1;

--3d point
SELECT ST_AsGeoJSON('LINESTRING(1 2 3, 4 5 6)'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsGML':
            self.label_17.setText("""ST_AsGML

Description
Return the geometry as a Geography Markup Language (GML) element. The version parameter, if specified, may be either 2 or 3. If no version parameter is specified then the default is assumed to be 2. The precision argument may be used to reduce the maximum number of decimal places (maxdecimaldigits) used in output (defaults to 15).
GML 2 refer to 2.1.2 version, GML 3 to 3.1.1 version
The 'options' argument is a bitfield. It could be used to define CRS output type in GML output, and to declare data as lat/lon:
• 0: GML Short CRS (e.g EPSG:4326), default value
• 1: GML Long CRS (e.g urn:ogc:def:crs:EPSG::4326)
• 2: For GML 3 only, remove srsDimension attribute from output.
• 4: For GML 3 only, use <LineString> rather than <Curve> tag for lines.
• 16: Declare that datas are lat/lon (e.g srid=4326). Default is to assume that data are planars. This option is useful for GML 3.1.1 output only, related to axis order. So if you set it, it will swap the coordinates so order is lat lon instead of database lon lat.
• 32: Output the box of the geometry (envelope).

Synopsis
text ST_AsGML(geometry geom, integer maxdecimaldigits=15, integer options=0);
text ST_AsGML(geography geog, integer maxdecimaldigits=15, integer options=0);
text ST_AsGML(integer version, geometry geom, integer maxdecimaldigits=15, integer options=0, text nprefix=null, text id=null);
text ST_AsGML(integer version, geography geog, integer maxdecimaldigits=15, integer options=0, text nprefix=null, text id=null);

Examples: Version 2
SELECT ST_AsGML(ST_GeomFromText('POLYGON((0 0,0 1,1 1,1 0,0 0))',4326));

Examples: Version 3
-- Flip coordinates and output extended EPSG (16 | 1)--
SELECT ST_AsGML(3, ST_GeomFromText('POINT(5.234234233242 6.34534534534)',4326), 5, 17); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsHEXEWKB':
            self.label_17.setText("""ST_AsHEXEWKB
            
Description
Returns a Geometry in HEXEWKB format (as text) using either little-endian (NDR) or big-endian (XDR) encoding. If no
encoding is specified, then NDR is used.

Synopsis
text ST_AsHEXEWKB(geometry g1, text NDRorXDR);
text ST_AsHEXEWKB(geometry g1);

Examples
SELECT ST_AsHEXEWKB(ST_GeomFromText('POLYGON((0 0,0 1,1 1,1 0,0 0))',4326));
which gives same answer as
SELECT ST_GeomFromText('POLYGON((0 0,0 1,1 1,1 0,0 0))',4326)::text; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsKML':
            self.label_17.setText("""ST_AsKML

Description
Return the geometry as a Keyhole Markup Language (KML) element. There are several variants of this function. maximum
number of decimal places used in output (defaults to 15), version default to 2 and default namespace is no prefix.

Synopsis
text ST_AsKML(geometry geom, integer maxdecimaldigits=15);
text ST_AsKML(geography geog, integer maxdecimaldigits=15);
text ST_AsKML(integer version, geometry geom, integer maxdecimaldigits=15, text nprefix=NULL);
text ST_AsKML(integer version, geography geog, integer maxdecimaldigits=15, text nprefix=NULL);

Examples
SELECT ST_AsKML(ST_GeomFromText('POLYGON((0 0,0 1,1 1,1 0,0 0))',4326));
--3d linestring
SELECT ST_AsKML('SRID=4326;LINESTRING(1 2 3, 4 5 6)'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsLatLonText':
            self.label_17.setText("""ST_AsLatLonText

ST_AsLatLonText — Return the Degrees, Minutes, Seconds representation of the given point.

Synopsis
text ST_AsLatLonText(geometry pt, text format=”);

Examples
SELECT (ST_AsLatLonText('POINT (-3.2342342 -2.32498)'));
SELECT (ST_AsLatLonText('POINT (-3.2342342 -2.32498)', 'D\textdegree{}M''S.SSS"C'));
SELECT (ST_AsLatLonText('POINT (-3.2342342 -2.32498)', 'D degrees, M minutes, S seconds to  the C')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsSVG':
            self.label_17.setText("""ST_AsSVG

Description
Return the geometry as Scalar Vector Graphics (SVG) path data. Use 1 as second argument to have the path data implemented in terms of relative moves, the default (or 0) uses absolute moves. Third argument may be used to reduce the maximum number of decimal digits used in output (defaults to 15). Point geometries will be rendered as cx/cy when 'rel' arg is 0, x/y when 'rel' is 1. Multipoint geometries are delimited by commas (","), GeometryCollection geometries are delimited by semicolons (";").

Synopsis
text ST_AsSVG(geometry geom, integer rel=0, integer maxdecimaldigits=15);
text ST_AsSVG(geography geog, integer rel=0, integer maxdecimaldigits=15);

Examples
SELECT ST_AsSVG(ST_GeomFromText('POLYGON((0 0,0 1,1 1,1 0,0 0))',4326)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsText':
            self.label_17.setText("""ST_AsText

Return the Well-Known Text (WKT) representation of the geometry/geography without SRID metadata.

Synopsis
text ST_AsText(geometry g1);
text ST_AsText(geography g1);

Examples
SELECT ST_AsText('01030000000100000005000000000000000000
000000000000000000000000000000000000000000000000
F03F000000000000F03F000000000000F03F000000000000F03
F000000000000000000000000000000000000000000000000'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AsTWKB':
            self.label_17.setText("""ST_AsTWKB

Description
Returns the geometry in TWKB (Tiny Well-Known Binary) format. TWKB is a compressed binary format with a focus on minimizing the size of the output.
The decimal digits parameters control how much precision is stored in the output. By default, values are rounded to the nearest unit before encoding. If you want to transfer more precision, increase the number. For example, a value of 1 implies that the first digit to the right of the decimal point will be preserved.
The sizes and bounding boxes parameters control whether optional information about the encoded length of the object and the bounds of the object are included in the output. By default they are not. Do not turn them on unless your client software has a use for them, as they just use up space (and saving space is the point of TWKB).
The array-input form of the function is used to convert a collection of geometries and unique identifiers into a TWKB collection that preserves the identifiers. This is useful for clients that expect to unpack a collection and then access further information about the objects inside. You can create the arrays using the array_agg function. The other parameters operate the same as for the simple form of the function.

Synopsis
bytea ST_AsTWKB(geometry g1, integer decimaldigits_xy=0, integer decimaldigits_z=0, integer decimaldigits_m=0, boolean include_sizes=false, boolean include_bounding boxes=false); bytea ST_AsTWKB(geometry[ ] geometries, bigint[ ] unique_ids, integer decimaldigits_xy=0, integer decimaldigits_z=0, integer decimaldigits_m=0, boolean include_sizes=false, boolean include_bounding_boxes=false);

Examples
SELECT ST_AsTWKB('LINESTRING(1 1,5 5)'::geometry);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_AsX3D':
            self.label_17.setText("""ST_AsX3D

Description
Returns a geometry as an X3D xml formatted node element http://www.web3d.org/standards/number/19776-1. If maxdecima ldigits (precision) is not specified then defaults to 15.
The 'options' argument is a bitfield. For PostGIS 2.2+, this is used to denote whether to represent coordinates with X3D GeoCoordinates Geospatial node and also whether to flip the x/y axis. By default, ST_AsX3D outputs in database form (long,lat or X,Y), but X3D default of lat/lon, y/x may be preferred.

Synopsis
text ST_AsX3D(geometry g1, integer maxdecimaldigits=15, integer options=0);

Example: An Octagon elevated 3 Units and decimal precision of 6
SELECT ST_AsX3D(ST_Translate( ST_Force_3d( ST_Buffer(ST_Point(10,10),5, 'quad_segs=2')), 0,0, 3) ,6) As x3dfrag;""")

        elif self.treeWidget.currentItem().text(0) == 'ST_GeoHash':
            self.label_17.setText("""ST_GeoHash

Description
Return a GeoHash representation (http://en.wikipedia.org/wiki/Geohash) of the geometry. A GeoHash encodes a point into a text form that is sortable and searchable based on prefixing. A shorter GeoHash is a less precise representation of a point. It can also be thought of as a box, that contains the actual point.
If no maxchars is specified ST_GeoHash returns a GeoHash based on full precision of the input geometry type. Points return a GeoHash with 20 characters of precision (about enough to hold the full double precision of the input). Other types return a
GeoHash with a variable amount of precision, based on the size of the feature. Larger features are represented with less precision, smaller features with more precision. The idea is that the box implied by the GeoHash will always contain the input feature. If maxchars is specified ST_GeoHash returns a GeoHash with at most that many characters so a possibly lower precision representation of the input geometry. For non-points, the starting point of the calculation is the center of the bounding box of the geometry.

Synopsis
text ST_GeoHash(geometry geom, integer maxchars=full_precision_of_point);

Examples
SELECT ST_GeoHash(ST_SetSRID(ST_MakePoint(-126,48),4326));
SELECT ST_GeoHash(ST_SetSRID(ST_MakePoint(-126,48),4326),5); """)

#8.9 Spatial Relationships and Measurements

        elif self.treeWidget.currentItem().text(0) == 'ST_3DClosestPoint':
            self.label_17.setText("""ST_3DClosestPoint

Description
Returns the 3-dimensional point on g1 that is closest to g2. This is the first point of the 3D shortest line. The 3D length of the
3D shortest line is the 3D distance.

Synopsis
geometry ST_3DClosestPoint(geometry g1, geometry g2);

Examples
linestring and point -- both 3d and 2d closest point
SELECT ST_AsEWKT(ST_3DClosestPoint(line,pt)) AS cp3d_line_pt, ST_AsEWKT(ST_ClosestPoint(line,pt)) As cp2d_line_pt
FROM (SELECT 'POINT(100 100 30)'::geometry As pt, 'LINESTRING (20 80 20, 98 190 1, 110 180 3, 50 75 1000)'::geometry As line) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_3DDistance':
            self.label_17.setText("""ST_3DDistance

Description
For geometry type returns the 3-dimensional minimum cartesian distance between two geometries in projected units (spatial ref units).

Synopsis
float ST_3DDistance(geometry g1, geometry g2);

Examples
-- Geometry example - units in meters (SRID: 2163 US National Atlas Equal area)(3D point and line compared 2D point and line)
-- Note: currently no vertical datum support so Z is not transformed and assumed to be same units as final.
SELECT ST_3DDistance(
ST_Transform(ST_GeomFromEWKT('SRID=4326;POINT(-72.1235 42.3521 4)'),2163),
ST_Transform(ST_GeomFromEWKT('SRID=4326;LINESTRING(-72.1260 42.45 15, -72.123 42.1546 20)'),2163)) As dist_3d,
ST_Distance(ST_Transform(ST_GeomFromText('POINT(-72.1235 42.3521)',4326),2163),ST_Transform(ST_GeomFromText('LINESTRING(-72.1260 42.45, -72.123 42.1546)', 4326) ,2163)) As dist_2d; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_3DDWithin':
            self.label_17.setText("""ST_3DDWithin

Description
For geometry type returns true if the 3d distance between two objects is within distance_of_srid specified projected units (spatial ref units).

Synopsis
boolean ST_3DDWithin(geometry g1, geometry g2, double precision distance_of_srid);

Examples
-- Geometry example - units in meters (SRID: 2163 US National Atlas Equal area) (3D point and line compared 2D point and line)
-- Note: currently no vertical datum support so Z is not transformed and assumed to be same units as final.
SELECT ST_3DDWithin(
ST_Transform(ST_GeomFromEWKT('SRID=4326;POINT(-72.1235 42.3521 4)'),2163),
ST_Transform(ST_GeomFromEWKT('SRID=4326;LINESTRING(-72.1260 42.45 15, -72.123 42.1546 20)'),2163), 126.8 ) As within_dist_3d,
ST_DWithin(ST_Transform(ST_GeomFromEWKT('SRID=4326;POINT(-72.1235 42.3521 4)'),2163),
ST_Transform(ST_GeomFromEWKT('SRID=4326;LINESTRING(-72.1260 42.45 15, -72.123 42.1546 20)'),2163), 126.8) As within_dist_2d; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_3DDFullyWithin':
            self.label_17.setText("""ST_3DDFullyWithin

Description
Returns true if the 3D geometries are fully within the specified distance of one another. The distance is specified in units defined by the spatial reference system of the geometries. For this function to make sense, the source geometries must both be of the same coordinate projection, having the same SRID.

Synopsis
boolean ST_3DDFullyWithin(geometry g1, geometry g2, double precision distance);

Examples
-- This compares the difference between fully within and distance within as well
-- as the distance fully within for the 2D footprint of the line/point vs. the 3d fully within
SELECT ST_3DDFullyWithin(geom_a, geom_b, 10) as D3DFullyWithin10, ST_3DDWithin(geom_a, geom_b, 10) as D3DWithin10,
ST_DFullyWithin(geom_a, geom_b, 20) as D2DFullyWithin20, ST_3DDFullyWithin(geom_a, geom_b, 20) as D3DFullyWithin20 from (select ST_GeomFromEWKT('POINT(1 1 2)') as geom_a,
ST_GeomFromEWKT('LINESTRING(1 5 2, 2 7 20, 1 9 100, 14 12 3)') as geom_b) t1; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_3DIntersects':
            self.label_17.setText("""ST_3DIntersects

Description
Overlaps, Touches, Within all imply spatial intersection. If any of the aforementioned returns true, then the geometries also spatially intersect. Disjoint implies false for spatial intersection.

Synopsis
boolean ST_3DIntersects( geometry geomA , geometry geomB );

Geometry Examples
SELECT ST_3DIntersects(pt, line), ST_Intersects(pt,line) FROM (SELECT 'POINT(0 0 2)'::geometry As pt, 'LINESTRING (0 0 1, 0 2 3 )'::geometry As line) As foo;

TIN Examples
set postgis.backend = sfcgal;
SELECT ST_3DIntersects('TIN(((0 0,1 0,0 1,0 0)))'::geometry, 'POINT(.1 .1)'::geometry); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_3DLongestLine':
            self.label_17.setText("""ST_3DLongestLine

Description
Returns the 3-dimensional longest line between two geometries. The function will only return the first longest line if more than one. The line returned will always start in g1 and end in g2. The 3D length of the line this function returns will always be the same as ST_3DMaxDistance returns for g1 and g2.

Synopsis
geometry ST_3DLongestLine(geometry g1, geometry g2);

Examples
SELECT ST_AsEWKT(ST_3DLongestLine(line,pt)) AS lol3d_line_pt, ST_AsEWKT(ST_LongestLine(line,pt)) As lol2d_line_pt
FROM (SELECT 'POINT(100 100 30)'::geometry As pt, 'LINESTRING (20 80 20, 98 190 1, 110 180 3, 50 75 1000)':: geometry As line) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_3DMaxDistance':
            self.label_17.setText("""ST_3DMaxDistance

Description
For geometry type returns the 3-dimensional maximum cartesian distance between two geometries in projected units (spatial ref units).

Synopsis
float ST_3DMaxDistance(geometry g1, geometry g2); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_3DShortestLine':
            self.label_17.setText("""ST_3DShortestLine

Description
Returns the 3-dimensional shortest line between two geometries. The function will only return the first shortest line if more than one, that the function finds. If g1 and g2 intersects in just one point the function will return a line with both start and end in that intersection-point. If g1 and g2 are intersecting with more than one point the function will return a line with start and end in the same point but it can be any of the intersecting points. The line returned will always start in g1 and end in g2. The 3D length of the line this function returns will always be the same as ST_3DDistance returns for g1 and g2.

Synopsis
geometry ST_3DShortestLine(geometry g1, geometry g2);

Examples
SELECT ST_AsEWKT(ST_3DShortestLine(line,pt)) AS shl3d_line_pt, ST_AsEWKT(ST_ShortestLine(line,pt)) As shl2d_line_pt
FROM (SELECT 'POINT(100 100 30)'::geometry As pt, 'LINESTRING (20 80 20, 98 190 1, 110 180 3, 50 75 1000)':: geometry As line ) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Area':
            self.label_17.setText("""ST_Area

Description
Returns the area of the geometry if it is a Polygon or MultiPolygon. Return the area measurement of an ST_Surface or ST_MultiSurface value. For geometry, a 2D Cartesian area is determined with units specified by the SRID. For geography, by default area is determined on a spheroid with units in square meters. To measure around the faster but less accurate sphere, use ST_Area(geog,false).

Synopsis
float ST_Area(geometry g1);
float ST_Area(geography geog, boolean use_spheroid=true);

Examples
SELECT ST_Area(the_geom) As sqft, ST_Area(the_geom)*POWER(0.3048,2) As sqm
FROM (SELECT ST_GeomFromText('POLYGON((743238 2967416,743238 2967450, 743265 2967450,743265.625 2967416,743238 2967416))',2249) ) As foo(the_geom); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Azimuth':
            self.label_17.setText("""ST_Azimuth

Description
Returns the azimuth in radians of the segment defined by the given point geometries, or NULL if the two points are coincident. The azimuth is angle is referenced from north, and is positive clockwise: North = 0; East = p/2; South = p; West = 3p/2.
For the geography type, the forward azimuth is solved as part of the inverse geodesic problem. The azimuth is mathematical concept defined as the angle between a reference plane and a point, with angular units in radians. Units can be converted to degrees using a built-in PostgreSQL function degrees(), as shown in the example.

Synopsis
float ST_Azimuth(geometry pointA, geometry pointB);
float ST_Azimuth(geography pointA, geography pointB);

Examples
Geometry Azimuth in degrees
SELECT degrees(ST_Azimuth(ST_Point(25, 45), ST_Point(75, 100))) AS degA_B, degrees(ST_Azimuth(ST_Point(75, 100), ST_Point(25, 45))) AS degB_A; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Centroid':
            self.label_17.setText("""ST_Centroid

Description
Computes the geometric center of a geometry, or equivalently, the center of mass of the geometry as a POINT. For [MULTI]POINTs, this is computed as the arithmetic mean of the input coordinates. For [MULTI]LINESTRINGs, this is computed as the weighted length of each line segment. For [MULTI]POLYGONs, "weight" is thought in terms of area. If an empty geometry is supplied, an empty GEOMETRYCOLLECTION is returned. If NULL is supplied, NULL is returned. If CIRCULARSTRING or COMPOUNDCURVE are supplied, they are converted to linestring wtih CurveToLine first, then same than for LINESTRING

Synopsis
geometry ST_Centroid(geometry g1);

Examples
SELECT ST_AsText(ST_Centroid('MULTIPOINT ( -1 0, -1 2, -1 3, -1 4, -1 7, 0 1, 0 3, 1 1, 2 0, 6 0, 7 8, 9 8, 10 6 )'));
SELECT ST_AsText(ST_centroid(g)) FROM ST_GeomFromText('CIRCULARSTRING(0 2, -1 1,0 0, 0.5 0, 1 0, 2 1, 1 2, 0.5 2, 0 2)') AS g ; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ClosestPoint':
            self.label_17.setText("""ST_ClosestPoint

Returns the 2-dimensional point on g1 that is closest to g2. This is the first point of the shortest line.

Synopsis
geometry ST_ClosestPoint(geometry g1, geometry g2);

Examples
SELECT ST_AsText(ST_ClosestPoint(pt,line)) AS cp_pt_line, ST_AsText(ST_ClosestPoint(line,pt)) As cp_line_pt FROM (SELECT 'POINT(100 100)'::geometry As pt, 'LINESTRING (20 80, 98 190, 110 180, 50 75 )'::geometry As line ) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ClusterDBSCAN':
            self.label_17.setText("""ST_ClusterDBSCAN

Description
Returns cluster number for each input geometry, based on a 2D implementation of the Density-based spatial clustering of applications with noise (DBSCAN) algorithm. Unlike ST_ClusterKMeans, it does not require the number of clusters to be specified, but instead uses the desired distance (eps) and density(minpoints) parameters to construct each cluster. An input geometry will be added to a cluster if it is either:
• A "core" geometry, that is within eps distance of at least minpoints other input geometries, or
• A "border" geometry, that is within eps distance of a core geometry.
Note that border geometries may be within eps distance of core geometries in more than one cluster; in this case, either assignment would be correct, and the border geometry will be arbitrarily asssigned to one of the available clusters. In these cases, it is possible for a correct cluster to be generated with fewer than minpoints geometries. When assignment of a border geometry is ambiguous, repeated calls to ST_ClusterDBSCAN will produce identical results if an ORDER BY clause is included in the window definition, but cluster assignments may differ from other implementations of the same algorithm.

Synopsis
integer ST_ClusterDBSCAN(geometry winset geom, float8 eps, integer minpoints);

Examples
Assigning a cluster number to each parcel point:
SELECT parcel_id, ST_ClusterDBSCAN(geom, eps := 0.5, minpoints := 5) over () AS cid FROM parcels;

Combining parcels with the same cluster number into a single geometry. This uses named argument calling
SELECT cid, ST_Collect(geom) AS cluster_geom, array_agg(parcel_id) AS ids_in_cluster FROM (
SELECT parcel_id, ST_ClusterDBSCAN(geom, eps := 0.5, minpoints := 5) over () AS cid, geom FROM parcels) sq GROUP BY cid; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ClusterIntersecting':
                    self.label_17.setText("""ST_ClusterIntersecting

Description
ST_ClusterIntersecting is an aggregate function that returns an array of GeometryCollections, where each GeometryCollection represents an interconnected set of geometries.

Synopsis
geometry[] ST_ClusterIntersecting(geometry set g);

Examples
WITH testdata AS
(SELECT unnest(ARRAY['LINESTRING (0 0, 1 1)'::geometry,
'LINESTRING (5 5, 4 4)'::geometry,
'LINESTRING (6 6, 7 7)'::geometry,
'LINESTRING (0 0, -1 -1)'::geometry,
'POLYGON ((0 0, 4 0, 4 4, 0 4, 0 0))'::geometry]) AS geom)
SELECT ST_AsText(unnest(ST_ClusterIntersecting(geom))) FROM testdata; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ClusterKMeans':
            self.label_17.setText("""ST_ClusterKMeans

Description
Returns 2D distance based k-means cluster number for each input geometry. The distance used for clustering is the distance between the centroids of the geometries.

Synopsis
integer ST_ClusterKMeans(geometry winset geom, integer number_of_clusters);

Examples
Generate dummy set of parcels for examples

CREATE TABLE parcels AS
SELECT lpad((row_number() over())::text,3,'0') As parcel_id, geom,
('{residential, commercial}'::text[])[1 + mod(row_number()OVER(),2)] As type
FROM
ST_Subdivide(ST_Buffer('LINESTRING(40 100, 98 100, 100 150, 60 90)'::geometry,
40, 'endcap=square'),12) As geom; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ClusterWithin':
            self.label_17.setText("""ST_ClusterWithin

Description
ST_ClusterWithin is an aggregate function that returns an array of GeometryCollections, where each GeometryCollection represents a set of geometries separated by no more than the specified distance.

Synopsis
geometry[ ] ST_ClusterWithin(geometry set g, float8 distance);

Examples
WITH testdata AS
(SELECT unnest(ARRAY['LINESTRING (0 0, 1 1)'::geometry,
'LINESTRING (5 5, 4 4)'::geometry,
'LINESTRING (6 6, 7 7)'::geometry,
'LINESTRING (0 0, -1 -1)'::geometry,
'POLYGON ((0 0, 4 0, 4 4, 0 4, 0 0))'::geometry]) AS geom)
SELECT ST_AsText(unnest(ST_ClusterWithin(geom, 1.4))) FROM testdata; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Contains':
            self.label_17.setText("""ST_Contains

Description
Geometry A contains Geometry B if and only if no points of B lie in the exterior of A, and at least one point of the interior of B lies in the interior of A. An important subtlety of this definition is that A does not contain its boundary, but A does contain itself.
Contrast that to ST_ContainsProperly where geometry A does not Contain Properly itself. Returns TRUE if geometry B is completely inside geometry A. For this function to make sense, the source geometries must both be of the same coordinate projection, having the same SRID. ST_Contains is the inverse of ST_Within. So ST_Contains(A,B) implies ST_Within(B,A) except in the case of invalid geometries where the result is always false regardless or not defined.

Synopsis
boolean ST_Contains(geometry geomA, geometry geomB);

Examples
-- A circle within a circle
SELECT ST_Contains(smallc, bigc) As smallcontainsbig,
ST_Contains(bigc,smallc) As bigcontainssmall,
ST_Contains(bigc, ST_Union(smallc, bigc)) as bigcontainsunion,
ST_Equals(bigc, ST_Union(smallc, bigc)) as bigisunion,
ST_Covers(bigc, ST_ExteriorRing(bigc)) As bigcoversexterior,
ST_Contains(bigc, ST_ExteriorRing(bigc)) As bigcontainsexterior
FROM (SELECT ST_Buffer(ST_GeomFromText('POINT(1 2)'), 10) As smallc,
ST_Buffer(ST_GeomFromText('POINT(1 2)'), 20) As bigc) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ContainsProperly':
            self.label_17.setText("""ST_ContainsProperly

Description
Returns true if B intersects the interior of A but not the boundary (or exterior). A does not contain properly itself, but does contain itself. Every point of the other geometry is a point of this geometry's interior. The DE-9IM Intersection Matrix for the two geometries matches [T**FF*FF*] used in ST_Relate

Synopsis
boolean ST_ContainsProperly(geometry geomA, geometry geomB);

Examples
--a circle within a circle
SELECT ST_ContainsProperly(smallc, bigc) As smallcontainspropbig,
ST_ContainsProperly(bigc,smallc) As bigcontainspropsmall,
ST_ContainsProperly(bigc, ST_Union(smallc, bigc)) as bigcontainspropunion,
ST_Equals(bigc, ST_Union(smallc, bigc)) as bigisunion,
ST_Covers(bigc, ST_ExteriorRing(bigc)) As bigcoversexterior,
ST_ContainsProperly(bigc, ST_ExteriorRing(bigc)) As bigcontainsexterior
FROM (SELECT ST_Buffer(ST_GeomFromText('POINT(1 2)'), 10) As smallc,
ST_Buffer(ST_GeomFromText('POINT(1 2)'), 20) As bigc) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Covers':
            self.label_17.setText("""ST_Covers

Description
Returns 1 (TRUE) if no point in Geometry/Geography B is outside Geometry/Geography A Performed by the GEOS module

Synopsis
boolean ST_Covers(geometry geomA, geometry geomB);
boolean ST_Covers(geography geogpolyA, geography geogpointB);

Examples
--a circle covering a circle
SELECT ST_Covers(smallc,smallc) As smallinsmall,
ST_Covers(smallc, bigc) As smallcoversbig,
ST_Covers(bigc, ST_ExteriorRing(bigc)) As bigcoversexterior,
ST_Contains(bigc, ST_ExteriorRing(bigc)) As bigcontainsexterior
FROM (SELECT ST_Buffer(ST_GeomFromText('POINT(1 2)'), 10) As smallc,
ST_Buffer(ST_GeomFromText('POINT(1 2)'), 20) As bigc) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_CoveredBy':
            self.label_17.setText("""ST_CoveredBy

Description
Returns 1 (TRUE) if no point in Geometry/Geography A is outside Geometry/Geography B Performed by the GEOS module

Synopsis
boolean ST_CoveredBy(geometry geomA, geometry geomB);
boolean ST_CoveredBy(geography geogA, geography geogB);

Examples
--a circle coveredby a circle
SELECT ST_CoveredBy(smallc,smallc) As smallinsmall,
ST_CoveredBy(smallc, bigc) As smallcoveredbybig,
ST_CoveredBy(ST_ExteriorRing(bigc), bigc) As exteriorcoveredbybig,
ST_Within(ST_ExteriorRing(bigc),bigc) As exeriorwithinbig
FROM (SELECT ST_Buffer(ST_GeomFromText('POINT(1 2)'), 10) As smallc,
ST_Buffer(ST_GeomFromText('POINT(1 2)'), 20) As bigc) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Crosses':
            self.label_17.setText("""ST_Crosses

Description
ST_Crosses takes two geometry objects and returns TRUE if their intersection "spatially cross", that is, the geometries have some, but not all interior points in common. The intersection of the interiors of the geometries must not be the empty set and must have a dimensionality less than the maximum dimension of the two input geometries. Additionally, the intersection of the two geometries must not equal either of the source geometries. Otherwise, it returns FALSE.

Synopsis
boolean ST_Crosses(geometry g1, geometry g2);

Examples
To determine a list of roads that cross a highway, use a query similiar to:
SELECT roads.id FROM roads, highways WHERE ST_Crosses(roads.the_geom, highways.the_geom); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_LineCrossingDirection':
            self.label_17.setText("""ST_LineCrossingDirection

Description
Given 2 linestrings, returns a number between -3 and 3 denoting what kind of crossing behavior. 0 is no crossing. This is only supported for LINESTRING

Synopsis
integer ST_LineCrossingDirection(geometry linestringA, geometry linestringB);

Examples
SELECT ST_LineCrossingDirection(foo.line1, foo.line2) As l1_cross_l2 ,
ST_LineCrossingDirection(foo.line2, foo.line1) As l2_cross_l1
FROM (SELECTST_GeomFromText('LINESTRING(25 169,89 114,40 70,86 43)') As line1,
ST_GeomFromText('LINESTRING(171 154,20 140,71 74,161 53)') As line2) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Disjoint':
            self.label_17.setText("""ST_Disjoint

Description
Overlaps, Touches, Within all imply geometries are not spatially disjoint. If any of the aforementioned returns true, then the geometries are not spatially disjoint. Disjoint implies false for spatial intersection. 

Synopsis
boolean ST_Disjoint( geometry A , geometry B );

Examples
SELECT ST_Disjoint('POINT(0 0)'::geometry, 'LINESTRING ( 2 0, 0 2 )'::geometry);
SELECT ST_Disjoint('POINT(0 0)'::geometry, 'LINESTRING ( 0 0, 0 2 )'::geometry); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Distance':
            self.label_17.setText("""ST_Distance

Description
For geometry type returns the minimum 2D Cartesian distance between two geometries in projected units (spatial ref units). For geography type defaults to return the minimum geodesic distance between two geographies in meters. If use_spheroid is false, a faster sphere calculation is used instead of a spheroid.

Synopsis
float ST_Distance(geometry g1, geometry g2);
float ST_Distance(geography gg1, geography gg2);
float ST_Distance(geography gg1, geography gg2, boolean use_spheroid);

Basic Geometry Examples
--Geometry example - units in planar degrees 4326 is WGS 84 long lat unit=degrees
SELECT ST_Distance(ST_GeomFromText('POINT(-72.1235 42.3521)',4326),ST_GeomFromText('LINESTRING(-72.1260 42.45, -72.123 42.1546)', 4326)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_MinimumClearance':
            self.label_17.setText("""ST_MinimumClearance

Description
It is not uncommon to have a geometry that, while meeting the criteria for validity according to ST_IsValid (polygons) or ST_IsSimple (lines), would become invalid if one of the vertices moved by a slight distance, as can happen during conversion to text-based formats (such as WKT, KML, GML GeoJSON), or binary formats that do not use double-precision floating point coordinates (MapInfo TAB).
A geometry's "minimum clearance" is the smallest distance by which a vertex of the geometry could be moved to produce an invalid geometry. It can be thought of as a quantitative measure of a geometry's robustness, where increasing values of minimum clearance indicate increasing robustness.
If a geometry has a minimum clearance of e, it can be said that:
• No two distinct vertices in the geometry are separated by less than e.
• No vertex is closer than e to a line segement of which it is not an endpoint.
If no minimum clearance exists for a geometry (for example, a single point, or a multipoint whose points are identical), then ST_MinimumClearance will return Infinity.

Synopsis
float ST_MinimumClearance(geometry g);

Examples
SELECT ST_MinimumClearance('POLYGON ((0 0, 1 0, 1 1, 0.5 3.2e-4, 0 0))'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_MinimumClearanceLine':
            self.label_17.setText("""ST_MinimumClearanceLine

Description            
Returns the two-point LineString spanning a geometry's minimum clearance. If the geometry does not have a minimum clearance, LINESTRING EMPTY will be returned.

Synopsis
Geometry ST_MinimumClearanceLine(geometry g);

Examples
SELECT ST_AsText(ST_MinimumClearanceLine('POLYGON ((0 0, 1 0, 1 1, 0.5 3.2e-4, 0 0))')); """)
    
        elif self.treeWidget.currentItem().text(0) == 'ST_HausdorffDistance':
            self.label_17.setText("""ST_HausdorffDistance

Description
Implements algorithm for computing a distance metric which can be thought of as the "Discrete Hausdorff Distance". This is the Hausdorff distance restricted to discrete points for one of the geometries. Wikipedia article on Hausdorff distance Martin Davis note on how Hausdorff Distance calculation was used to prove correctness of the CascadePolygonUnion approach. When densifyFrac is specified, this function performs a segment densification before computing the discrete hausdorff distance. The densifyFrac parameter sets the fraction by which to densify each segment. Each segment will be split into a number of equal-length subsegments, whose fraction of the total length is closest to the given fraction.

Synopsis
float ST_HausdorffDistance(geometry g1, geometry g2);
float ST_HausdorffDistance(geometry g1, geometry g2, float densifyFrac);

Examples
SELECT DISTINCT ON(buildings.gid) buildings.gid, parcels.parcel_id
FROM buildings INNER JOIN parcels ON ST_Intersects(buildings.geom,parcels.geom)
ORDER BY buildings.gid, ST_HausdorffDistance(buildings.geom, parcels.geom); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_MaxDistance':
            self.label_17.setText("""ST_MaxDistance

Returns the 2-dimensional largest distance between two geometries in projected units.

Synopsis
float ST_MaxDistance(geometry g1, geometry g2);

Examples
SELECT ST_MaxDistance('POINT(0 0)'::geometry, 'LINESTRING ( 2 0, 0 2 )'::geometry);
SELECT ST_MaxDistance('POINT(0 0)'::geometry, 'LINESTRING ( 2 2, 2 2 )'::geometry); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_DistanceSphere':
            self.label_17.setText("""ST_DistanceSphere

Description
Returns minimum distance in meters between two lon/lat points. Uses a spherical earth and radius derived from the spheroid defined by the SRID. Faster than ST_DistanceSpheroid, but less accurate. PostGIS Versions prior to 1.5 only implemented for points.

Synopsis
float ST_DistanceSphere(geometry geomlonlatA, geometry geomlonlatB);

Examples
SELECT st_distance_sphere(st_point(-69.23, 44.61), st_point(-75.42, 43.55)) """)

        elif self.treeWidget.currentItem().text(0) == 'ST_DistanceSpheroid':
            self.label_17.setText("""ST_DistanceSpheroid

Description
Returns minimum distance in meters between two lon/lat geometries given a particular spheroid. See the explanation of spheroids given for ST_LengthSpheroid. PostGIS version prior to 1.5 only support points.

Synopsis
float ST_DistanceSpheroid(geometry geomlonlatA, geometry geomlonlatB, spheroid measurement_spheroid); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_DFullyWithin':
            self.label_17.setText("""ST_DFullyWithin

Description
Returns true if the geometries is fully within the specified distance of one another. The distance is specified in units defined by the spatial reference system of the geometries. For this function to make sense, the source geometries must both be of the same coordinate projection, having the same SRID.

Synopsis
boolean ST_DFullyWithin(geometry g1, geometry g2, double precision distance);

Examples
SELECT ST_DFullyWithin(geom_a, geom_b, 10) as DFullyWithin10, ST_DWithin(geom_a, geom_b, 10) as DWithin10, ST_DFullyWithin(geom_a, geom_b, 20) as DFullyWithin20 from (select ST_GeomFromText('POINT(1 1)') as geom_a,ST_GeomFromText('LINESTRING(1 5, 2 7, 1 9, 14 12)') as geom_b) t1;
""")
        elif self.treeWidget.currentItem().text(0) == 'ST_DWithin':
            self.label_17.setText("""ST_DWithin

Description
Returns true if the geometries are within the specified distance of one another. For Geometries: The distance is specified in units defined by the spatial reference system of the geometries. For this function to make sense, the source geometries must both be of the same coordinate projection, having the same SRID. For geography units are in meters and measurement is defaulted to use_spheroid=true, for faster check, use_spheroid=false to measure along sphere.

Synopsis
boolean ST_DWithin(geometry g1, geometry g2, double precision distance_of_srid);
boolean ST_DWithin(geography gg1, geography gg2, double precision distance_meters);
boolean ST_DWithin(geography gg1, geography gg2, double precision distance_meters, boolean use_spheroid);

Examples
SELECT DISTINCT ON (s.gid) s.gid, s.school_name, s.the_geom, h.hospital_name
FROM schools s LEFT JOIN hospitals h ON ST_DWithin(s.the_geom, h.the_geom, 3000) ORDER BY s.gid, ST_Distance(s.the_geom, h.the_geom);""")

        elif self.treeWidget.currentItem().text(0) == 'ST_Equals':
            self.label_17.setText("""ST_Equals

Description
Returns TRUE if the given Geometries are "spatially equal". Use this for a 'better' answer than '='. Note by spatially equal we mean ST_Within(A,B) = true and ST_Within(B,A) = true and also mean ordering of points can be different but represent the same geometry structure. To verify the order of points is consistent, use ST_OrderingEquals (it must be noted ST_OrderingEquals is a little more stringent than simply verifying order of points are the same).

Synopsis
boolean ST_Equals(geometry A, geometry B);

Examples
SELECT ST_Equals(ST_GeomFromText('LINESTRING(0 0, 10 10)'), ST_GeomFromText('LINESTRING(0 0, 5 5, 10 10)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_GeometricMedian':
            self.label_17.setText("""ST_GeometricMedian
            
Description
Computes the approximate geometric median of a MultiPoint geometry using the Weiszfeld algorithm. The geometric median provides a centrality measure that is less sensitive to outlier points than the centroid. The algorithm will iterate until the distance change between successive iterations is less than the supplied tolerance parameter. If this condition has not been met after max_iterations iterations, the function will produce an error and exit, unless fail_if_not_converged is set to false. If a tolerance value is not provided, a default tolerance value will be calculated based on the extent of the input geometry.

Synopsis
geometry ST_GeometricMedian ( geometry g , float8 tolerance , int max_iter , boolean fail_if_not_converged );

Examples

WITH test AS ( SELECT 'MULTIPOINT((0 0), (1 1), (2 2), (200 200))'::geometry geom)
SELECT ST_AsText(ST_Centroid(geom)) centroid, ST_AsText(ST_GeometricMedian(geom)) median FROM test; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_HasArc':
            self.label_17.setText("""ST_HasArc

Description
Returns true if a geometry or geometry collection contains a circular string

Synopsis
boolean ST_HasArc(geometry geomA);

Examples
SELECT ST_HasArc(ST_Collect('LINESTRING(1 2, 3 4, 5 6)', 'CIRCULARSTRING(1 1, 2 3, 4 5, 6 7, 5 6)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Intersects':
            self.label_17.setText("""ST_Intersects

Description
If a geometry or geography shares any portion of space then they intersect. For geography -- tolerance is 0.00001 meters (so any points that are close are considered to intersect) Overlaps, Touches, Within all imply spatial intersection. If any of the aforementioned returns true, then the geometries also spatially intersect. Disjoint implies false for spatial intersection.

Synopsis
boolean ST_Intersects( geometry geomA , geometry geomB );
boolean ST_Intersects( geography geogA , geography geogB );

Geometry Examples
SELECT ST_Intersects('POINT(0 0)'::geometry, 'LINESTRING ( 2 0, 0 2 )'::geometry);

Geography Examples
SELECT ST_Intersects(
ST_GeographyFromText('SRID=4326;LINESTRING(-43.23456 72.4567,-43.23456 72.4568)'), ST_GeographyFromText('SRID=4326;POINT(-43.23456 72.4567772)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Length':
            self.label_17.setText("""ST_Length

Description
For geometry: Returns the 2D Cartesian length of the geometry if it is a LineString, MultiLineString, ST_Curve, ST_MultiCurve. 0 is returned for areal geometries. For areal geometries use ST_Perimeter. For geometry types, units for length measures are specified by the spatial reference system of the geometry.
For geography types, the calculations are performed using the inverse geodesic problem, where length units are in meters. If PostGIS is compiled with PROJ version 4.8.0 or later, the spheroid is specified by the SRID, otherwise it is exclusive to WGS84. If use_spheroid=false, then calculations will approximate a sphere instead of a spheroid. Currently for geometry this is an alias for ST_Length2D, but this may change to support higher dimensions.

Synopsis
float ST_Length(geometry a_2dlinestring);
float ST_Length(geography geog, boolean use_spheroid=true);

Geometry Examples
--Return length in feet for line string. Note this is in feet because EPSG:2249 is Massachusetts State Plane Feet
SELECT ST_Length(ST_GeomFromText('LINESTRING(743238 2967416,743238 2967450,743265 2967450, 743265.625 2967416,743238 2967416)',2249));

Geography Examples
--Return length of WGS 84 geography line
-- default calculation is using a sphere rather than spheroid
SELECT ST_Length(the_geog) As length_spheroid, ST_Length(the_geog,false) As length_sphere FROM (SELECT ST_GeographyFromText('SRID=4326;LINESTRING(-72.1260 42.45, -72.1240 42.45666, -72.123 42.1546)') As the_geog) As foo;
""")
        elif self.treeWidget.currentItem().text(0) == 'ST_Length2D':
            self.label_17.setText("""ST_Length2D
        
Description
Returns the 2-dimensional length of the geometry if it is a linestring or multi-linestring. This is an alias for ST_Length

Synopsis
float ST_Length2D(geometry a_2dlinestring); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_3DLength':
            self.label_17.setText("""ST_3DLength

Description
Returns the 3-dimensional or 2-dimensional length of the geometry if it is a linestring or multi-linestring. For 2-d lines it will just return the 2-d length (same as ST_Length and ST_Length2D)

Synopsis
float ST_3DLength(geometry a_3dlinestring);

Examples
SELECT ST_3DLength(ST_GeomFromText('LINESTRING(743238 2967416 1,743238 2967450 1,743265 2967450 3, 743265.625 2967416 3,743238 2967416 3)',2249));
 """)

        elif self.treeWidget.currentItem().text(0) == 'ST_LengthSpheroid':
            self.label_17.setText("""ST_LengthSpheroid

Description
Calculates the length/perimeter of a geometry on an ellipsoid. This is useful if the coordinates of the geometry are in longitude/ latitude and a length is desired without reprojection. The ellipsoid is a separate database type and can be constructed as follows:
SPHEROID[<NAME>,<SEMI-MAJOR AXIS>,<INVERSE FLATTENING>]
SPHEROID["GRS_1980",6378137,298.257222101]

Synopsis
float ST_LengthSpheroid(geometry a_geometry, spheroid a_spheroid); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Length2D_Spheroid':
            self.label_17.setText("""ST_Length2D_Spheroid

Description
Calculates the 2D length/perimeter of a geometry on an ellipsoid. This is useful if the coordinates of the geometry are in longitude/latitude and a length is desired without reprojection. The ellipsoid is a separate database type and can be constructed as follows:
SPHEROID[<NAME>,<SEMI-MAJOR AXIS>,<INVERSE FLATTENING>]
SPHEROID["GRS_1980",6378137,298.257222101]

Synopsis
float ST_Length2D_Spheroid(geometry a_geometry, spheroid a_spheroid); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_LongestLine':
            self.label_17.setText("""ST_LongestLine

Description
Returns the 2-dimensional longest line points of two geometries. The function will only return the first longest line if more than one, that the function finds. The line returned will always start in g1 and end in g2. The length of the line this function returns will always be the same as st_maxdistance returns for g1 and g2.

Synopsis
geometry ST_LongestLine(geometry g1, geometry g2);

Examples
SELECT ST_AsText( ST_LongestLine('POINT(100 100)':: geometry, 'LINESTRING (20 80, 98 190, 110 180, 50 75 )'::geometry)) As lline;
SELECT ST_AsText(ST_LongestLine(ST_GeomFromText('POLYGON ((175 150, 20 40, 50 60, 125 100, 175 150))'), ST_Buffer(ST_GeomFromText ('POINT(110 170)'), 20))) As llinewkt;
""")
        elif self.treeWidget.currentItem().text(0) == 'ST_OrderingEquals':
            self.label_17.setText("""ST_OrderingEquals

Description
ST_OrderingEquals compares two geometries and returns t (TRUE) if the geometries are equal and the coordinates are in the same order; otherwise it returns f (FALSE).

Synopsis
boolean ST_OrderingEquals(geometry A, geometry B);

Examples
SELECT ST_OrderingEquals(ST_GeomFromText('LINESTRING(0 0, 10 10)'), ST_GeomFromText('LINESTRING(0 0, 5 5, 10 10)'));
SELECT ST_OrderingEquals(ST_Reverse(ST_GeomFromText('LINESTRING(0 0, 10 10)')), ST_GeomFromText('LINESTRING(0 0, 0 0, 10 10)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Overlaps':
            self.label_17.setText("""ST_Overlaps

Description
Returns TRUE if the Geometries "spatially overlap". By that we mean they intersect, but one does not completely contain another. Performed by the GEOS module This function call will automatically include a bounding box comparison that will make use of any indexes that are available on the geometries. To avoid index use, use the function _ST_Overlaps.

Synopsis
boolean ST_Overlaps(geometry A, geometry B);

Examples
SELECT ST_Overlaps(a,b) As a_overlap_b, ST_Crosses(a,b) As a_crosses_b, ST_Intersects(a, b) As a_intersects_b, ST_Contains(b,a) As b_contains_a
FROM (SELECT ST_GeomFromText('POINT(1 0.5)') As a, ST_GeomFromText('LINESTRING(1 0, 1 1, 3 5)') As b) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Perimeter':
            self.label_17.setText("""ST_Perimeter

Description
Returns the 2D perimeter of the geometry/geography if it is a ST_Surface, ST_MultiSurface (Polygon, MultiPolygon). 0 is returned for non-areal geometries. For linear geometries use ST_Length. For geometry types, units for perimeter measures are specified by the spatial reference system of the geometry.
For geography types, the calculations are performed using the inverse geodesic problem, where perimeter units are in meters. If PostGIS is compiled with PROJ version 4.8.0 or later, the spheroid is specified by the SRID, otherwise it is exclusive to WGS84. If use_spheroid=false, then calculations will approximate a sphere instead of a spheroid. Currently this is an alias for ST_Perimeter2D, but this may change to support higher dimensions.

Synopsis
float ST_Perimeter(geometry g1);
float ST_Perimeter(geography geog, boolean use_spheroid=true);

Examples: Geometry
SELECT ST_Perimeter(ST_GeomFromText('POLYGON((743238 2967416,743238 2967450,743265 2967450, 743265.625 2967416,743238 2967416))', 2249));

Examples: Geography

SELECT ST_Perimeter(geog) As per_meters, ST_Perimeter(geog)/0.3048 As per_ft
FROM ST_GeogFromText('POLYGON((-71.1776848522251 42.3902896512902,-71.1776843766326 42.3903829478009, -71.1775844305465 42.3903826677917,-71.1775825927231 42.3902893647987,-71.1776848522251 42.3902896512902))') As geog;
""")

        elif self.treeWidget.currentItem().text(0) == 'ST_Perimeter2D':
            self.label_17.setText("""ST_Perimeter2D

Description
Returns the 2-dimensional perimeter of the geometry, if it is a polygon or multi-polygon.

Synopsis
float ST_Perimeter2D(geometry geomA); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_3DPerimeter':
            self.label_17.setText("""ST_3DPerimeter

Description
Returns the 3-dimensional perimeter of the geometry, if it is a polygon or multi-polygon. If the geometry is 2-dimensional, then the 2-dimensional perimeter is returned.

Synopsis
float ST_3DPerimeter(geometry geomA);

Examples
--Perimeter of a slightly elevated polygon in the air in Massachusetts state plane feet
SELECT ST_3DPerimeter(the_geom), ST_Perimeter2d(the_geom), ST_Perimeter(the_geom) FROM (SELECT ST_GeomFromEWKT('SRID=2249;POLYGON((743238 2967416 2,743238 2967450 1, 743265.625 2967416 1,743238 2967416 2))') As the_geom) As foo;
""")
        elif self.treeWidget.currentItem().text(0) == 'ST_PointOnSurface':
            self.label_17.setText("""ST_PointOnSurface

Returns a POINT guaranteed to lie on the surface.

Synopsis
geometry ST_PointOnSurface(geometry g1);

Examples
SELECT ST_AsText(ST_PointOnSurface('POINT(0 5)'::geometry));
SELECT ST_AsText(ST_PointOnSurface('LINESTRING(0 5, 0 10)'::geometry));
SELECT ST_AsText(ST_PointOnSurface('POLYGON((0 0, 0 5, 5 5, 5 0, 0 0))'::geometry)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Project':
            self.label_17.setText("""ST_Project

Description
Returns a POINT projected along a geodesic from a start point using an azimuth (bearing) measured in radians and distance measured in meters. This is also called a direct geodesic problem.
The azimuth is sometimes called the heading or the bearing in navigation. It is measured relative to true north (azimuth zero). East is azimuth 90 (p/2), south is azimuth 180 (p), west is azimuth 270 (3p/2). The distance is given in meters.

Synopsis
geography ST_Project(geography g1, float distance, float azimuth);

Example: Using degrees - projected point 100,000 meters and bearing 45 degrees
SELECT ST_AsText(ST_Project('POINT(0 0)'::geography, 100000, radians(45.0))); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Relate':
            self.label_17.setText("""ST_Relate

Description
Version 1: Takes geomA, geomB, intersectionMatrix and Returns 1 (TRUE) if this Geometry is spatially related to anotherGeometry, by testing for intersections between the Interior, Boundary and Exterior of the two geometries as specified by the values in the DE-9IM matrix pattern. This is especially useful for testing compound checks of intersection, crosses, etc in one step. Do not call with a GeometryCollection as an argument

Synopsis
boolean ST_Relate(geometry geomA, geometry geomB, text intersectionMatrixPattern);
text ST_Relate(geometry geomA, geometry geomB);
text ST_Relate(geometry geomA, geometry geomB, integer BoundaryNodeRule);

Examples
SELECT ST_Relate(ST_GeometryFromText('LINESTRING(1 2, 3 4)'), ST_GeometryFromText('LINESTRING(5 6, 7 8)'));
SELECT ST_Relate(ST_GeometryFromText('POINT(1 2)'), ST_Buffer(ST_GeometryFromText('POINT(1 2)'),2), '0FFFFF212'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_RelateMatch':
            self.label_17.setText("""ST_RelateMatch

Description
Takes intersectionMatrix and intersectionMatrixPattern and Returns true if the intersectionMatrix satisfies the intersectionMatrixPattern.

Synopsis
boolean ST_RelateMatch(text intersectionMatrix, text intersectionMatrixPattern);

Examples
SELECT ST_RelateMatch('101202FFF', 'TTTTTTFFF'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ShortestLine':
            self.label_17.setText("""ST_ShortestLine
            
Description
Returns the 2-dimensional shortest line between two geometries. The function will only return the first shortest line if more than one, that the function finds. If g1 and g2 intersects in just one point the function will return a line with both start and end in that intersection-point. If g1 and g2 are intersecting with more than one point the function will return a line with start and end in the same point but it can be any of the intersecting points. The line returned will always start in g1 and end in g2. The length of the line this function returns will always be the same as ST_Distance returns for g1 and g2.            
            
Synopsis
geometry ST_ShortestLine(geometry g1, geometry g2);            
            
Examples
SELECT ST_AsText(ST_ShortestLine('POINT(100 100) '::geometry, 'LINESTRING (20 80, 98  - 190, 110 180, 50 75 )'::geometry) ) As sline;
SELECT ST_AsText(ST_ShortestLine(ST_GeomFromText( 'POLYGON((175 150, 20 40, 50 60, 125 ST_Buffer(ST_GeomFromText('POINT(110 170)'), 20))) As slinewkt; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Touches':
            self.label_17.setText("""ST_Touches

Description
Returns TRUE if the only points in common between g1 and g2 lie in the union of the boundaries of g1 and g2. The ST_To uches relation applies to all Area/Area, Line/Line, Line/Area, Point/Area and Point/Line pairs of relationships, but not to the Point/Point pair.

Synopsis
boolean ST_Touches(geometry g1, geometry g2);

Examples
SELECT ST_Touches('LINESTRING(0 0, 1 1, 0 2)'::geometry, 'POINT(1 1)'::geometry);
SELECT ST_Touches('LINESTRING(0 0, 1 1, 0 2)'::geometry, 'POINT(0 2)'::geometry); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Within':
            self.label_17.setText("""ST_Within

Description
Returns TRUE if geometry A is completely inside geometry B. For this function to make sense, the source geometries must both be of the same coordinate projection, having the same SRID. It is a given that if ST_Within(A,B) is true and ST_Within(B,A) is true, then the two geometries are considered spatially equal.

Synopsis
boolean ST_Within(geometry A, geometry B);

Examples
--a circle within a circle
SELECT ST_Within(smallc,smallc) As smallinsmall,
ST_Within(smallc, bigc) As smallinbig,
ST_Within(bigc,smallc) As biginsmall,
ST_Within(ST_Union(smallc, bigc), bigc) as unioninbig,
ST_Within(bigc, ST_Union(smallc, bigc)) as biginunion,
ST_Equals(bigc, ST_Union(smallc, bigc)) as bigisunion
FROM ( SELECT ST_Buffer(ST_GeomFromText('POINT(50 50)'), 20) As smallc,
ST_Buffer(ST_GeomFromText('POINT(50 50)'), 40) As bigc) As foo; """)

#8.11 Geometry Processing
        elif self.treeWidget.currentItem().text(0) == 'ST_Buffer':
            self.label_17.setText("""ST_Buffer

Description
Returns a geometry/geography that represents all points whose distance from this Geometry/geography is less than or equal to distance. Geometry: Calculations are in the Spatial Reference System of the geometry. Introduced in 1.5 support for different end cap and mitre settings to control shape.

Synopsis
geometry ST_Buffer(geometry g1, float radius_of_buffer);
geometry ST_Buffer(geometry g1, float radius_of_buffer, integer num_seg_quarter_circle);
geometry ST_Buffer(geometry g1, float radius_of_buffer, text buffer_style_parameters);
geography ST_Buffer(geography g1, float radius_of_buffer_in_meters);
geography ST_Buffer(geography g1, float radius_of_buffer, integer num_seg_quarter_circle);
geography ST_Buffer(geography g1, float radius_of_buffer, text buffer_style_parameters);

Examples
SELECT ST_Buffer(geom, 50, 'quad_segs=2') from tabelleName;
SELECT ST_Buffer(ST_GeomFromText('POINT(100 90)'), 50, 'quad_segs=8');
SELECT ST_Buffer(ST_GeomFromText('POINT(100 90)'), 50, 'quad_segs=2');
SELECT ST_Buffer(ST_GeomFromText('LINESTRING(50 50,150 150,150 50)'), 10, 'endcap=round join=round');
SELECT ST_Buffer(ST_GeomFromText('LINESTRING(50 50,150 150,150 50)'), 10, 'endcap=square join=round'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_BuildArea':
            self.label_17.setText("""ST_BuildArea

Description
Creates an areal geometry formed by the constituent linework of given geometry. The return type can be a Polygon or Multi- Polygon, depending on input. If the input lineworks do not form polygons NULL is returned. The inputs can be LINESTRINGS, MULTILINESTRINGS, POLYGONS, MULTIPOLYGONS, and GeometryCollections.
            
Synopsis
geometry ST_BuildArea(geometry A);

Examples
SELECT ST_BuildArea(ST_Collect(smallc,bigc)) FROM (SELECT ST_Buffer( ST_GeomFromText('POINT(100 90)'), 25) As smallc, ST_Buffer(ST_GeomFromText('POINT(100 90)'), 50) As bigc) As foo;
""")

        elif self.treeWidget.currentItem().text(0) == 'ST_ClipByBox2D':
            self.label_17.setText("""ST_ClipByBox2D

Description
Clips a geometry by a 2D box in a fast but possibly dirty way. The output geometry is not guaranteed to be valid (self-intersections for a polygon may be introduced). Topologically invalid input geometries do not result in exceptions being thrown.

Synopsis
geometry ST_ClipByBox2D(geometry geom, box2d box);

Examples
-- Rely on implicit cast from geometry to box2d for the second parameter
SELECT ST_ClipByBox2D(the_geom, ST_MakeEnvelope(0,0,10,10)) FROM mytab; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Collect':
            self.label_17.setText("""ST_Collect

Description
Output type can be a MULTI* or a GEOMETRYCOLLECTION. Comes in 2 variants. Variant 1 collects 2 geometries. Variant 2 is an aggregate function that takes a set of geometries and collects them into a single ST_Geometry.
Aggregate version: This function returns a GEOMETRYCOLLECTION or a MULTI object from a set of geometries. The ST_Collect() function is an "aggregate" function in the terminology of PostgreSQL. That means that it operates on rows of data, in the same way the SUM() and AVG() functions do. For example, "SELECT ST_Collect(GEOM) FROM GEOMTABLE GROUP BY ATTRCOLUMN" will return a separate GEOMETRYCOLLECTION for each distinct value of ATTRCOLUMN.
Non-Aggregate version: This function returns a geometry being a collection of two input geometries. Output type can be a MULTI* or a GEOMETRYCOLLECTION.

Synopsis
geometry ST_Collect(geometry set g1field);
geometry ST_Collect(geometry g1, geometry g2);
geometry ST_Collect(geometry[] g1_array);

Examples
SELECT gid, address, category, ST_Collect(geom) from tabel_name group by gid, category
SELECT stusps, ST_Multi(ST_Collect(f.the_geom)) as singlegeom FROM (SELECT stusps, (ST_Dump(the_geom)).geom As the_geom FROM somestatetable ) As f GROUP BY stusps
SELECT ST_AsText(ST_Collect(ST_GeomFromText('POINT(1 2)'), ST_GeomFromText('POINT(-2 3)') )); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ConcaveHull':
            self.label_17.setText("""ST_ConcaveHull

Description
The concave hull of a geometry represents a possibly concave geometry that encloses all geometries within the set. Defaults to false for allowing polygons with holes. The result is never higher than a single polygon.
The target_percent is the target percent of area of convex hull the PostGIS solution will try to approach before giving up or exiting. One can think of the concave hull as the geometry you get by vacuum sealing a set of geometries. The target_percent of 1 will give you the same answer as the convex hull. A target_percent between 0 and 0.99 will give you something that should have a smaller area than the convex hull. This is different from a convex hull which is more like wrapping a rubber band around the set of geometries.
It is usually used with MULTI and Geometry Collections. Although it is not an aggregate - you can use it in conjunction with ST_Collect or ST_Union to get the concave hull of a set of points/linestring/polygons ST_ConcaveHull(ST_Collect(somepointfield), 0.80).

Synopsis
geometry ST_ConcaveHull(geometry geomA, float target_percent, boolean allow_holes=false);

Examples
--Get estimate of infected area based on point observations
SELECT d.disease_type, ST_ConcaveHull(ST_Collect(d.pnt_geom), 0.99) As geom FROM disease_obs As d GROUP BY d.disease_type; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ConvexHull':
            self.label_17.setText("""ST_ConvexHull
            
Description
The convex hull of a geometry represents the minimum convex geometry that encloses all geometries within the set. One can think of the convex hull as the geometry you get by wrapping an elastic band around a set of geometries. This is different from a concave hull which is analogous to shrink-wrapping your geometries. It is usually used with MULTI and Geometry Collections. Although it is not an aggregate - you can use it in conjunction with ST_Collect to get the convex hull of a set of points. ST_ConvexHull(ST_Collect(somepointfield)). It is often used to determine an affected area based on a set of point observations.            

Synopsis
geometry ST_ConvexHull(geometry geomA);

Examples
--Get estimate of infected area based on point observations
SELECT d.disease_type, ST_ConvexHull(ST_Collect(d.the_geom)) As the_geom FROM disease_obs As d GROUP BY d.disease_type; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_CurveToLine':
            self.label_17.setText("""ST_CurveToLine

Description
Converst a CIRCULAR STRING to regular LINESTRING or CURVEPOLYGON to POLYGON. Useful for outputting to devices that can't support CIRCULARSTRING geometry types Converts a given geometry to a linear geometry. Each curved geometry or segment is converted into a linear approximation using the default value of 32 segments per quarter circle

Synopsis
geometry ST_CurveToLine(geometry curveGeom);
geometry ST_CurveToLine(geometry curveGeom, integer segments_per_qtr_circle);

Examples
SELECT ST_AsText(ST_CurveToLine(ST_GeomFromText('CIRCULARSTRING(220268 150415,220227 150505,220227 150406)')));
--3d example
SELECT ST_AsEWKT(ST_CurveToLine(ST_GeomFromEWKT('CIRCULARSTRING(220268 150415 1,220227 150505 2,220227 150406 3)'))); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_DelaunayTriangles':
            self.label_17.setText("""ST_DelaunayTriangles

Description
Return a Delaunay triangulation around the vertices of the input geometry. Output is a COLLECTION of polygons (for flags=0) or a MULTILINESTRING (for flags=1) or TIN (for flags=2). The tolerance, if any, is used to snap input vertices togheter.

Synopsis
geometry ST_DelaunayTriangles(geometry g1, float tolerance, int4 flags);

Examples
ST_Union(ST_GeomFromText('POLYGON((175 150, 20 40, 50 60, 125 100, 175 150))'), ST_Buffer(ST_GeomFromText('POINT(110 170)'), 20)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Difference':
            self.label_17.setText("""ST_Difference

Description
Returns a geometry that represents that part of geometry A that does not intersect with geometry B. One can think of this as GeometryA - ST_Intersection(A,B). If A is completely contained in B then an empty geometry collection is returned.

Synopsis
geometry ST_Difference(geometry geomA, geometry geomB);

Examples
SELECT ST_AsText( ST_Difference( ST_GeomFromText('LINESTRING(50 100, 50 200)'), ST_GeomFromText('LINESTRING(50 50, 50 150)'))); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Dump':
            self.label_17.setText("""ST_Dump

Description
This is a set-returning function (SRF). It returns a set of geometry_dump rows, formed by a geometry (geom) and an array of integers (path). When the input geometry is a simple type (POINT,LINESTRING,POLYGON) a single record will be returned with an empty path array and the input geometry as geom. When the input geometry is a collection or multi it will return a record for each of the collection components, and the path will express the position of the component inside the collection. ST_Dump is useful for expanding geometries. It is the reverse of a GROUP BY in that it creates new rows. For example it can be use to expand MULTIPOLYGONS into POLYGONS.

Synopsis
geometry_dump[] ST_Dump(geometry g1);

Examples
SELECT sometable.field1, sometable.field1, (ST_Dump(sometable.the_geom)).geom AS the_geom FROM sometable; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_DumpPoints':
            self.label_17.setText("""ST_DumpPoints

Description
This set-returning function (SRF) returns a set of geometry_dump rows formed by a geometry (geom) and an array of integers (path).
The geom component of geometry_dump are all the POINTs that make up the supplied geometry The path component of geometry_dump (an integer[]) is an index reference enumerating the POINTs of the supplied geometry. For example, if a LINESTRING is supplied, a path of {i} is returned where i is the nth coordinate in the LINEST RING. If a POLYGON is supplied, a path of {i,j} is returned where i is the ring number (1 is outer; inner rings follow) and j enumerates the POINTs (again 1-based index).

Synopsis
geometry_dump[]ST_DumpPoints(geometry geom);

Examples
SELECT edge_id, (dp).path[1] As index, ST_AsText((dp).geom) As wktnode
FROM (SELECT 1 As edge_id , ST_DumpPoints(ST_GeomFromText('LINESTRING(1 2, 3 4, 10 10)')) AS dp
UNION ALL SELECT 2 As edge_id , ST_DumpPoints(ST_GeomFromText('LINESTRING(3 5, 5 6, 9 10)')) AS dp) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_DumpRings':
            self.label_17.setText("""ST_DumpRings

Description
This is a set-returning function (SRF). It returns a set of geometry_dump rows, defined as an integer[] and a geometry, aliased "path" and "geom" respectively. The "path" field holds the polygon ring index containing a single integer: 0 for the shell, >0 for holes. The "geom" field contains the corresponding ring as a polygon.

Synopsis
geometry_dump[] ST_DumpRings(geometry a_polygon);

Examples
SELECT sometable.field1, sometable.field1, (ST_DumpRings(sometable.the_geom)).geom As the_geom FROM sometableOfpolys; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_FlipCoordinates':
            self.label_17.setText("""ST_FlipCoordinates

Returns a version of the given geometry with X and Y axis flipped. Useful for people who have built latitude/longitude features and need to fix them.

Synopsis
geometry ST_FlipCoordinates(geometry geom);

Example
SELECT ST_AsEWKT(ST_FlipCoordinates(GeomFromEWKT('POINT(1 2)'))); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_GeneratePoints':
            self.label_17.setText("""ST_GeneratePoints

Description
ST_GeneratePoints generates pseudo-random points until the requested number are found within the input area.

Synopsis
geometry ST_GeneratePoints( g geometry , npoints numeric );

SELECT ST_GeneratePoints( ST_Buffer( ST_GeomFromText( 'LINESTRING(50 50,150 150,150 50)'), 10, 'endcap=round join =round'), 12); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Intersection':
            self.label_17.setText("""ST_Intersection

Description
Returns a geometry that represents the point set intersection of the Geometries. In other words - that portion of geometry A and geometry B that is shared between the two geometries. If the geometries do not share any space (are disjoint), then an empty geometry collection is returned. ST_Intersection in conjunction with ST_Intersects is very useful for clipping geometries such as in bounding box, buffer, region queries where you only want to return that portion of a geometry that sits in a country or region of interest.

Synopsis
geometry ST_Intersection( geometry geomA , geometry geomB );
geography ST_Intersection( geography geogA , geography geogB );

Examples
SELECT ST_AsText(ST_Intersection('POINT(0 0)'::geometry, 'LINESTRING ( 2 0, 0 2 )':: geometry));

SELECT clipped.gid, clipped.f_name, clipped_geom FROM (SELECT trails.gid, trails.f_name, (ST_Dump(ST_Intersection(country.the_geom, trails. the_geom))).geom As clipped_geom
FROM country INNER JOIN trails ON ST_Intersects(country.the_geom, trails.the_geom)) As clipped WHERE ST_Dimension(clipped.clipped_geom) = 1 ; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_LineToCurve':
            self.label_17.setText("""ST_LineToCurve

Description
Converts plain LINESTRING/POLYGONS to CIRCULAR STRINGs and Curved Polygons. Note much fewer points are needed to describe the curved equivalent.

Synopsis
geometry ST_LineToCurve(geometry geomANoncircular);

SELECT ST_AsText(ST_LineToCurve(foo.the_geom)) As curvedastext,ST_AsText(foo.the_geom) As  non_curvedastext FROM (SELECT ST_Buffer('POINT(1 3)'::geometry, 3) As the_geom) As foo;

SELECT ST_AsEWKT(ST_LineToCurve(ST_GeomFromEWKT('LINESTRING(1 2 3, 3 4 8, 5 6 4, 7 8 4, 9 10 4)'))); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_MakeValid':
            self.label_17.setText("""ST_MakeValid

Description
The function attempts to create a valid representation of a given invalid geometry without losing any of the input vertices. Already-valid geometries are returned without further intervention.
Supported inputs are: POINTS, MULTIPOINTS, LINESTRINGS, MULTILINESTRINGS, POLYGONS, MULTIPOLYGONS and GEOMETRYCOLLECTIONS containing any mix of them.
In case of full or partial dimensional collapses, the output geometry may be a collection of lower-to-equal dimension geometries or a geometry of lower dimension. Single polygons may become multi-geometries in case of self-intersections.

Synopsis
geometry ST_MakeValid(geometry input); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_MemUnion':
            self.label_17.setText("""ST_MemUnion

Same as ST_Union, only memory-friendly (uses less memory and more processor time).

Synopsis
geometry ST_MemUnion(geometry set geomfield); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_MinimumBoundingCircle':
            self.label_17.setText("""ST_MinimumBoundingCircle

Description
Returns the smallest circle polygon that can fully contain a geometry. It is often used with MULTI and Geometry Collections. Although it is not an aggregate - you can use it in conjunction with ST_Collect to get the minimum bounding circle of a set of geometries. ST_MinimumBoundingCircle(ST_Collect(somepointfield)). The ratio of the area of a polygon divided by the area of its Minimum Bounding Circle is often referred to as the Roeck test.

Synopsis
geometry ST_MinimumBoundingCircle(geometry geomA, integer num_segs_per_qt_circ=48);

Examples
SELECT d.disease_type, ST_MinimumBoundingCircle(ST_Collect(d.the_geom)) As the_geom FROM disease_obs As d GROUP BY d.disease_type; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_MinimumBoundingRadius':
            self.label_17.setText("""ST_MinimumBoundingRadius

Description
Returns a record containing the center point and radius of the smallest circle that can fully contain a geometry. Can be used in conjunction with ST_Collect to get the minimum bounding circle of a set of geometries.

Synopsis
(geometry, double precision) ST_MinimumBoundingRadius(geometry geom);

Examples
SELECT ST_AsText(center), radius FROM ST_MinimumBoundingRadius('POLYGON((26426 65078,26531 65242,26075 65136,26096 65427,26426 65078))'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Polygonize':
            self.label_17.setText("""ST_Polygonize

Aggregate. Creates a GeometryCollection containing possible polygons formed from the constituent linework of a set of geometries.

Synopsis
geometry ST_Polygonize(geometry set geomfield);
geometry ST_Polygonize(geometry[] geom_array);

Examples: Polygonizing single linestrings
SELECT ST_AsEWKT(ST_Polygonize(the_geom_4269)) As geomtextrep FROM (SELECT the_geom_4269 FROM ma.suffolk_edges ORDER BY tlid LIMIT 45) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Node':
            self.label_17.setText("""ST_Node

Description
Fully node a set of linestrings using the least possible number of nodes while preserving all of the input ones.

Synopsis
geometry ST_Node(geometry geom);

Examples
SELECT ST_AsEWKT( ST_Node('LINESTRINGZ(0 0 0, 10 10 10, 0 10 5, 10 0 3)'::geometry) ) As output; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_OffsetCurve':
            self.label_17.setText("""ST_OffsetCurve

Description
Return an offset line at a given distance and side from an input line. All points of the returned geometries are not further than the given distance from the input geometry. For positive distance the offset will be at the left side of the input line and retain the same direction. For a negative distance it'll be at the right side and in the opposite direction. Availability: 2.0 - requires GEOS >= 3.2, improved with GEOS >= 3.3 The optional third parameter allows specifying a list of blank-separated key=value pairs to tweak operations as follows:
• 'quad_segs=#' : number of segments used to approximate a quarter circle (defaults to 8).
• 'join=round|mitre|bevel' : join style (defaults to "round"). 'miter' is also accepted as a synonym for 'mitre'.
• 'mitre_limit=#.#' : mitre ratio limit (only affects mitred join style). 'miter_limit' is also accepted as a synonym for 'mitre_limit'.

Synopsis
geometry ST_OffsetCurve(geometry line, float signed_distance, text style_parameters=”);

Examples --Compute an open buffer around roads
SELECT ST_Union(
ST_OffsetCurve(f.the_geom, f.width/2, 'quad_segs=4 join=round'),
ST_OffsetCurve(f.the_geom, -f.width/2, 'quad_segs=4 join=round')
) as track FROM someroadstable; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_RemoveRepeatedPoints':
            self.label_17.setText("""ST_RemoveRepeatedPoints

Description
Returns a version of the given geometry with duplicated points removed. Will actually do something only with (multi)lines, (multi)polygons and multipoints but you can safely call it with any kind of geometry. Since simplification occurs on a object-by object basis you can also feed a GeometryCollection to this function.
If the tolerance parameter is provided, vertices within the tolerance of one another will be considered the "same" for the purposes of removal.

Synopsis
geometry ST_RemoveRepeatedPoints(geometry geom, float8 tolerance); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_SharedPaths':
            self.label_17.setText("""ST_SharedPaths

Description
Returns a collection containing paths shared by the two input geometries. Those going in the same direction are in the first element of the collection, those going in the opposite direction are in the second element. The paths themselves are given in the direction of the first geometry.

Synopsis
geometry ST_SharedPaths(geometry lineal1, geometry lineal2);

SELECT ST_AsText( ST_SharedPaths(
ST_GeomFromText('MULTILINESTRING((26 125,26 200,126 200,126 125,26 125),
(51 150,101 150,76 175,51 150))'), ST_GeomFromText('LINESTRING(151 100,126 156.25,126 125,90 161, 76 175)'))) As wkt; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ShiftLongitude':
            self.label_17.setText("""ST_ShiftLongitude

Description
Reads every point/vertex in every component of every feature in a geometry, and if the longitude coordinate is <0, adds 360 to it. The result would be a 0-360 version of the data to be plotted in a 180 centric map

Synopsis
geometry ST_ShiftLongitude(geometry geomA);

Examples
--3d points
SELECT ST_AsEWKT(ST_ShiftLongitude(ST_GeomFromEWKT('SRID=4326;POINT(-118.58 38.38 10)'))) As geomA,
ST_AsEWKT(ST_ShiftLongitude(ST_GeomFromEWKT('SRID=4326;POINT(241.42 38.38 10)'))) As geomb

--regular line string
SELECT ST_AsText(ST_ShiftLongitude(ST_GeomFromText('LINESTRING(-118.58 38.38, -118.20 38.45)'))) """)

        elif self.treeWidget.currentItem().text(0) == 'ST_WrapX':
            self.label_17.setText("""ST_WrapX

Description
This function splits the input geometries and then moves every resulting component falling on the right (for negative 'move') or on the left (for positive 'move') of given 'wrap' line in the direction specified by the 'move' parameter, finally re-unioning the pieces togheter.

Synopsis
geometry ST_WrapX(geometry geom, float8 wrap, float8 move);

Description
This function splits the input geometries and then moves every resulting component falling on the right (for negative 'move') or on the left (for positive 'move') of given 'wrap' line in the direction specified by the 'move' parameter, finally re-unioning the pieces togheter.

Examples
-- Move all components of the given geometries whose bounding box
-- falls completely on the left of x=0 to +360
select ST_WrapX(the_geom, 0, 360);

-- Move all components of the given geometries whose bounding box
-- falls completely on the left of x=-30 to +360
select ST_WrapX(the_geom, -30, 360); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Simplify':
            self.label_17.setText("""ST_Simplify

Description
Returns a "simplified" version of the given geometry using the Douglas-Peucker algorithm. Will actually do something only with (multi)lines and (multi)polygons but you can safely call it with any kind of geometry. Since simplification occurs on a object-by-object basis you can also feed a GeometryCollection to this function.
The "preserve collapsed" flag will retain objects that would otherwise be too small given the tolerance. For example, a 1m long line simplified with a 10m tolerance. If the preserve flag is given, the line will not disappear. This flag is useful for rendering engines, to avoid having large numbers of very small objects disappear from a map leaving surprising gaps.

Synopsis
geometry ST_Simplify(geometry geomA, float tolerance, boolean preserveCollapsed); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_SimplifyPreserveTopology':
            self.label_17.setText("""ST_SimplifyPreserveTopology

Description
Returns a "simplified" version of the given geometry using the Douglas-Peucker algorithm. Will avoid creating derived geometries (polygons in particular) that are invalid. Will actually do something only with (multi)lines and (multi)polygons but you can safely call it with any kind of geometry. Since simplification occurs on a object-by-object basis you can also feed a GeometryCollection to this function.

Synopsis
geometry ST_SimplifyPreserveTopology(geometry geomA, float tolerance); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_SimplifyVW':
            self.label_17.setText("""ST_SimplifyVW

Description
Returns a "simplified" version of the given geometry using the Visvalingam-Whyatt algorithm. Will actually do something only with (multi)lines and (multi)polygons but you can safely call it with any kind of geometry. Since simplification occurs on a object-by-object basis you can also feed a GeometryCollection to this function.

Synopsis
geometry ST_SimplifyVW(geometry geomA, float tolerance);

Examples
A LineString is simplified with a minimum area threshold of 30.
SELECT ST_AsText(ST_SimplifyVW(geom,30)) simplified FROM (SELECT 'LINESTRING(5 2, 3 8, 6 20, 7 25, 10 10)'::geometry geom) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_SetEffectiveArea':
            self.label_17.setText("""ST_SetEffectiveArea

Description
Sets the effective area for each vertex, using the Visvalingam-Whyatt algorithm. The effective area is stored as the M-value of the vertex. If the optional "theshold" parameter is used, a simplified geometry will be returned, containing only vertices with an effective area greater than or equal to the threshold value. This function can be used for server-side simplification when a threshold is specified. Another option is to use a threshold value of zero. In this case, the full geometry will be returned with effective areas as M-values, which can be used by the client to simplify very quickly. Will actually do something only with (multi)lines and (multi)polygons but you can safely call it with any kind of geometry. Since simplification occurs on a object-by-object basis you can also feed a GeometryCollection to this function.

Synopsis
geometry ST_SetEffectiveArea(geometry geomA, float threshold = 0, integer set_area = 1);

Examples

select ST_AsText(ST_SetEffectiveArea(geom)) all_pts, ST_AsText(ST_SetEffectiveArea(geom,30)) thrshld_30 FROM (SELECT 'LINESTRING(5 2, 3 8, 6 20, 7 25, 10 10)'::geometry geom) As foo;
""")
        elif self.treeWidget.currentItem().text(0) == 'ST_Split':
            self.label_17.setText("""ST_Split

Description
The function supports splitting a line by (multi)point, (multi)line or (multi)polygon boundary, a (multi)polygon by line. The returned geometry is always a collection. Think of this function as the opposite of ST_Union. Theoretically applying ST_Union to the elements of the returned collection should always yield the original geometry.

Synopsis
geometry ST_Split(geometry input, geometry blade);

Examples
-- this creates a geometry collection consisting of the 2 halves of the polygon
-- this is similar to the example we demonstrated in ST_BuildArea
SELECT ST_Split(circle, line) FROM (SELECT ST_MakeLine(ST_MakePoint(10, 10),ST_MakePoint(190, 190)) As line, ST_Buffer(ST_GeomFromText('POINT(100 90)'), 50) As circle) As foo;
""")
        elif self.treeWidget.currentItem().text(0) == 'ST_SymDifference':
            self.label_17.setText("""ST_SymDifference

Description
Returns a geometry that represents the portions of A and B that do not intersect. It is called a symmetric difference because ST_SymDifference(A,B) = ST_SymDifference(B,A). One can think of this as ST_Union(geomA,geomB) - ST_Intersection(A,B).

Synopsis
geometry ST_SymDifference(geometry geomA, geometry geomB);

Examples

--Safe for 2d - symmetric difference of 2 linestrings
SELECT ST_AsText(ST_SymDifference( ST_GeomFromText('LINESTRING(50 100, 50 200)'), ST_GeomFromText('LINESTRING(50 50, 50 150)'))); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Subdivide':
            self.label_17.setText("""ST_Subdivide

Description
Turns a single geometry into a set in which each element has fewer than the maximum allowed number of vertices. Useful for converting excessively large polygons and other objects into small portions that fit within the database page size. Uses the same envelope clipping as ST_ClipByBox2D does, recursively subdividing the input geometry until all portions have less than the maximum vertex count. Minimum vertice count allowed is 8 and if you try to specify lower than 8, it will throw an error.

Synopsis
setof geometry ST_Subdivide(geometry geom, integer max_vertices=256);

Examples
-- Create a new subdivided table suitable for joining to the original
CREATE TABLE subdivided_geoms AS SELECT pkey, ST_Subdivide(geom) AS geom FROM original_geoms; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_SwapOrdinates':
            self.label_17.setText("""ST_SwapOrdinates

Description
Returns a version of the given geometry with given ordinates swapped. The ords parameter is a 2-characters string naming the ordinates to swap. Valid names are: x,y,z and m.

Synopsis
geometry ST_SwapOrdinates(geometry geom, cstring ords);

Example
-- Scale M value by 2
SELECT ST_AsText( ST_SwapOrdinates( ST_Scale( ST_SwapOrdinates(g,'xm'), 2, 1 ), 'xm')) FROM ( SELECT 'POINT ZM (0 0 0 2)'::geometry g ) foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Union':
            self.label_17.setText("""ST_Union

Description
Output type can be a MULTI*, single geometry, or Geometry Collection. Comes in 2 variants. Variant 1 unions 2 geometries resulting in a new geometry with no intersecting regions. Variant 2 is an aggregate function that takes a set of geometries and unions them into a single ST_Geometry resulting in no intersecting regions.
Aggregate version: This function returns a MULTI geometry or NON-MULTI geometry from a set of geometries. The ST_Union() function is an "aggregate" function in the terminology of PostgreSQL. That means that it operates on rows of data, in the same way the SUM() and AVG() functions do and like most aggregates, it also ignores NULL geometries. Non-Aggregate version: This function returns a geometry being a union of two input geometries. Output type can be a MULTI*, NON-MULTI or GEOMETRYCOLLECTION. If any are NULL, then NULL is returned.

Synopsis
geometry ST_Union(geometry set g1field);
geometry ST_Union(geometry g1, geometry g2);
geometry ST_Union(geometry[] g1_array);

Examples
SELECT stusps, ST_Multi(ST_Union(f.the_geom)) as singlegeom FROM sometable As f GROUP BY stusps """)

        elif self.treeWidget.currentItem().text(0) == 'ST_UnaryUnion':
            self.label_17.setText("""ST_UnaryUnion

Description
Unlike ST_Union, ST_UnaryUnion does dissolve boundaries between components of a multipolygon (invalid) and does performunion between the components of a geometrycollection. Each components of the input geometry is assumed to be valid, so you won't get a valid multipolygon out of a bow-tie polygon (invalid).
You may use this function to node a set of linestrings. You may mix ST_UnaryUnion with ST_Collect to fine-tune how many geometries at once you want to dissolve to be nice on both memory size and CPU time, finding the balance between ST_Union and ST_MemUnion.

Synopsis
geometry ST_UnaryUnion(geometry geom); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_VoronoiLines':
            self.label_17.setText("""ST_VoronoiLines

Description
ST_VoronoiLines computes a two-dimensional Voronoi diagram from the vertices of the supplied geometry and returns the boundaries between cells in that diagram as a MultiLineString.
Optional parameters:
• 'tolerance' : The distance within which vertices will be considered equivalent. Robustness of the algorithm can be improved by supplying a nonzero tolerance distance. (default = 0.0)
• 'extend_to' : If a geometry is supplied as the "extend_to" parameter, the diagram will be extended to cover the envelope of the "extend_to" geometry, unless that envelope is smaller than the default envelope. (default = NULL)

Synopsis
geometry ST_VoronoiLines( g1 geometry , tolerance float8 , extend_to geometry );

Examples
SELECT ST_VoronoiLines(geom, 30) As geomFROM (SELECT 'MULTIPOINT (50 30, 60 30, 100 100,10 150, 110 120)'::geometry As geom ) As g; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_VoronoiPolygons':
            self.label_17.setText("""ST_VoronoiPolygons

Description
ST_VoronoiPolygons computes a two-dimensional Voronoi diagram from the vertices of the supplied geometry. The result is a GeometryCollection of Polygons that covers an envelope larger than the extent of the input vertices.
Optional parameters:
• 'tolerance' : The distance within which vertices will be considered equivalent. Robustness of the algorithm can be improved by supplying a nonzero tolerance distance. (default = 0.0)
• 'extend_to' : If a geometry is supplied as the "extend_to" parameter, the diagram will be extended to cover the envelope of the "extend_to" geometry, unless that envelope is smaller than the default envelope. (default = NULL)

Synopsis
geometry ST_VoronoiPolygons( g1 geometry , tolerance float8 , extend_to geometry );

SELECT
ST_VoronoiPolygons(geom) As geom FROM (SELECT 'MULTIPOINT (50 30, 60 30, 100 100,10 150, 110 120)'::geometry As geom ) As g; """)

#8.12 Linear Referencing
        elif self.treeWidget.currentItem().text(0) == 'ST_LineInterpolatePoint':
            self.label_17.setText("""ST_LineInterpolatePoint

Description
Returns a point interpolated along a line. First argument must be a LINESTRING. Second argument is a float8 between 0 and 1 representing fraction of total linestring length the point has to be located. See ST_LineLocatePoint for computing the line location nearest to a Point.

Synopsis
geometry ST_LineInterpolatePoint(geometry a_linestring, float8 a_fraction);

Examples
--Return point 20% along 2d line
SELECT ST_AsEWKT(ST_LineInterpolatePoint(the_line, 0.20)) FROM (SELECT ST_GeomFromEWKT('LINESTRING(25 50, 100 125, 150 190)') as the_line) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_LineLocatePoint':
            self.label_17.setText("""ST_LineLocatePoint

Description
Returns a float between 0 and 1 representing the location of the closest point on LineString to the given Point, as a fraction of total 2d line length. You can use the returned location to extract a Point (ST_LineInterpolatePoint) or a substring (ST_LineSubstring). This is useful for approximating numbers of addresses

Synopsis
float8 ST_LineLocatePoint(geometry a_linestring, geometry a_point); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_LineSubstring':
            self.label_17.setText("""ST_LineSubstring

Description
Return a linestring being a substring of the input one starting and ending at the given fractions of total 2d length. Second and third arguments are float8 values between 0 and 1. This only works with LINESTRINGs. To use with contiguous MULTILINESTRINGs use in conjunction with ST_LineMerge. If 'start' and 'end' have the same value this is equivalent to ST_LineInterpolatePoint. See ST_LineLocatePoint for computing the line location nearest to a Point.

Synopsis
geometry ST_LineSubstring(geometry a_linestring, float8 startfraction, float8 endfraction);

Examples

--Return the approximate 1/3 mid-range part of a linestring
SELECT ST_AsText(ST_Line_SubString(ST_GeomFromText('LINESTRING(25 50, 100 125, 150 190)'), 0.333, 0.666)); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_LocateAlong':
            self.label_17.setText("""ST_LocateAlong

Description
Return a derived geometry collection value with elements that match the specified measure. Polygonal elements are not supported. If an offset is provided, the resultant will be offset to the left or right of the input line by the specified number of units. A positive offset will be to the left, and a negative one to the right. Semantic is specified by: ISO/IEC CD 13249-3:200x(E) - Text for Continuation CD Editing Meeting

Synopsis
geometry ST_LocateAlong(geometry ageom_with_measure, float8 a_measure, float8 offset);

Examples
SELECT ST_AsText(the_geom) FROM (SELECT ST_LocateAlong( ST_GeomFromText('MULTILINESTRINGM((1 2 3, 3 4 2, 9 4 3), (1 2 3, 5 4 5))'),3) As the_geom) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_LocateBetween':
            self.label_17.setText("""ST_LocateBetween

Description
Return a derived geometry collection value with elements that match the specified range of measures inclusively. Polygonal elements are not supported. Semantic is specified by: ISO/IEC CD 13249-3:200x(E) - Text for Continuation CD Editing Meeting Availability: 1.1.0 by old name ST_Locate_Between_Measures. Changed: 2.0.0 - in prior versions this used to be called ST_Locate_Between_Measures. The old name has been deprecated and will be removed in the future but is still available for backward compatibility.

Synopsis
geometry ST_LocateBetween(geometry geomA, float8 measure_start, float8 measure_end, float8 offset);

Examples
SELECT ST_AsText(the_geom) FROM (SELECT ST_LocateBetween( ST_GeomFromText('MULTILINESTRING M ((1 2 3, 3 4 2, 9 4 3), (1 2 3, 5 4 5))'),1.5, 3) As the_geom) As foo;
""")
        elif self.treeWidget.currentItem().text(0) == 'ST_LocateBetweenElevations':
            self.label_17.setText("""ST_LocateBetweenElevations

Description
Return a derived geometry (collection) value with elements that intersect the specified range of elevations inclusively. Only 3D, 3DM LINESTRINGS and MULTILINESTRINGS are supported.

Synopsis
geometry ST_LocateBetweenElevations(geometry geom_mline, float8 elevation_start, float8 elevation_end);

Examples
SELECT ST_AsEWKT(ST_LocateBetweenElevations( ST_GeomFromEWKT('LINESTRING(1 2 3, 4 5 6)'),2,4)) As ewelev; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_InterpolatePoint':
            self.label_17.setText("""ST_InterpolatePoint

Description
Return the value of the measure dimension of a geometry at the point closed to the provided point.

Synopsis
float8 ST_InterpolatePoint(geometry line, geometry point);

Examples
SELECT ST_InterpolatePoint('LINESTRING M (0 0 0, 10 0 20)', 'POINT(5 5)'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_AddMeasure':
            self.label_17.setText("""ST_AddMeasure

Description
Return a derived geometry with measure elements linearly interpolated between the start and end points. If the geometry has no measure dimension, one is added. If the geometry has a measure dimension, it is over-written with new values. Only LINESTRINGS and MULTILINESTRINGS are supported.

Synopsis
geometry ST_AddMeasure(geometry geom_mline, float8 measure_start, float8 measure_end);

Examples
SELECT ST_AsText(ST_AddMeasure( ST_GeomFromEWKT('LINESTRING(1 0, 2 0, 4 0)'),1,4)) As ewelev; """)

#8.13 Temporal Support
        elif self.treeWidget.currentItem().text(0) == 'ST_IsValidTrajectory':
            self.label_17.setText("""ST_IsValidTrajectory

Description
Tell if a geometry encodes a valid trajectory. Valid trajectories are encoded as LINESTRING with M value growing from each vertex to the next. Valid trajectories are expected as input to some spatio-temporal queries like ST_ClosestPointOfApproach

Synopsis
boolean ST_IsValidTrajectory(geometry line);

Examples
-- A valid trajectory
SELECT ST_IsValidTrajectory(ST_MakeLine( ST_MakePointM(0,0,1), ST_MakePointM(0,1,2))); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_ClosestPointOfApproach':
            self.label_17.setText("""ST_ClosestPointOfApproach

Description
Returns the smallest measure at which point interpolated along the given lines are at the smallest distance. Inputs must be valid trajectories as checked by ST_IsValidTrajectory. Null is returned if the trajectories do not overlap on the M range. See ST_LocateAlong for getting the actual points at the given measure.

Synopsis
float8 ST_ClosestPointOfApproach(geometry track1, geometry track2); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_DistanceCPA':
            self.label_17.setText("""ST_DistanceCPA

Description
Returns the minimum distance two moving objects have ever been each-other. Inputs must be valid trajectories as checked by ST_IsValidTrajectory. Null is returned if the trajectories do not overlap on the M range.

Synopsis
float8 ST_DistanceCPA(geometry track1, geometry track2); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_CPAWithin':
            self.label_17.setText("""ST_CPAWithin

Description
Checks whether two moving objects have ever been within the specified max distance. Inputs must be valid trajectories as checked by ST_IsValidTrajectory. False is returned if the trajectories do not overlap on the M range.

Synopsis
float8 ST_CPAWithin(geometry track1, geometry track2, float8 maxdist); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Accum':
            self.label_17.setText("""ST_Accum

Description
Aggregate. Constructs an array of geometries.

Synopsis
geometry[ ] ST_Accum(geometry set geomfield);

Examples
SELECT (ST_Accum(the_geom)) As all_em, ST_AsText((ST_Accum(the_geom))[1]) As grabone, (ST_Accum(the_geom))[2:4] as grab_rest
FROM (SELECT ST_MakePoint(a*CAST(random()*10 As integer), a*CAST(random()*10 As integer), a*CAST(random()*10 As integer)) As the_geom FROM generate_series(1,4) a) As foo; """)
 
        elif self.treeWidget.currentItem().text(0) == 'Box2D':
            self.label_17.setText("""Box2D
            
Description
Returns a BOX2D representing the maximum extents of the geometry.

Synopsis
box2d Box2D(geometry geomA);

Examples
SELECT Box2D(ST_GeomFromText('LINESTRING(1 2, 3 4, 5 6)'));
SELECT Box2D(ST_GeomFromText('CIRCULARSTRING(220268 150415,220227 150505,220227 150406)')); """)

        elif self.treeWidget.currentItem().text(0) == 'Box3D':
            self.label_17.setText("""Box3D

Returns a BOX3D representing the maximum extents of the geometry.

Synopsis
box3d Box3D(geometry geomA);

Examples
SELECT Box3D(ST_GeomFromEWKT('LINESTRING(1 2 3, 3 4 5, 5 6 5)'));
SELECT Box3D(ST_GeomFromEWKT('CIRCULARSTRING(220268 150415 1,220227 150505 1,220227 150406 1)')); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_EstimatedExtent':
            self.label_17.setText("""ST_EstimatedExtent

Description
Return the 'estimated' extent of the given spatial table. The estimated is taken from the geometry column's statistics. The current schema will be used if not specified. The default behavior is to also use statistics collected from children tables (tables with INHERITS) if available. If 'parent_ony' is set to TRUE, only statistics for the given table are used and children tables are ignored.
For PostgreSQL>=8.0.0 statistics are gathered by VACUUM ANALYZE and resulting extent will be about 95% of the real one.

Synopsis
box2d ST_EstimatedExtent(text schema_name, text table_name, text geocolumn_name, boolean parent_ony);
box2d ST_EstimatedExtent(text schema_name, text table_name, text geocolumn_name);
box2d ST_EstimatedExtent(text table_name, text geocolumn_name);

Examples
SELECT ST_EstimatedExtent('ny', 'edges', 'the_geom');
SELECT ST_EstimatedExtent('feature_poly', 'the_geom'); """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Expand':
            self.label_17.setText("""ST_Expand

Description
This function returns a bounding box expanded from the bounding box of the input, either by specifying a single distance with which the box should be expanded in all directions, or by specifying an expansion distance for each direction. Uses doubleprecision.
Can be very useful for distance queries, or to add a bounding box filter to a query to take advantage of a spatial index.
In addition to the geometry version of ST_Expand, which is the most commonly used, variants are provided that accept and produce internal BOX2D and BOX3D data types. ST_Expand is similar in concept to ST_Buffer, except while buffer expands the geometry in all directions, ST_Expand expands the bounding box an x,y,z unit amount.
Units are in the units of the spatial reference system in use denoted by the SRID.

Synopsis
geometry ST_Expand(geometry geom, float units_to_expand);
geometry ST_Expand(geometry geom, float dx, float dy, float dz=0, float dm=0);
box2d ST_Expand(box2d box, float units_to_expand);
box2d ST_Expand(box2d box, float dx, float dy);
box3d ST_Expand(box3d box, float units_to_expand);
box3d ST_Expand(box3d box, float dx, float dy, float dz=0);

Examples

--10 meter expanded box around bbox of a linestring
SELECT CAST(ST_Expand(ST_GeomFromText('LINESTRING(2312980 110676,2312923 110701,2312892 110714)', 2163),10) As box2d);
--10 meter expanded 3d box of a 3d box
SELECT ST_Expand(CAST('BOX3D(778783 2951741 1,794875 2970042.61545891 10)' As box3d),10) """)

        elif self.treeWidget.currentItem().text(0) == 'ST_Extent':
            self.label_17.setText("""ST_Extent

Description
ST_Extent returns a bounding box that encloses a set of geometries. The ST_Extent function is an "aggregate" function in the terminology of SQL. That means that it operates on lists of data, in the same way the SUM() and AVG() functions do.
Since it returns a bounding box, the spatial Units are in the units of the spatial reference system in use denoted by the SRID ST_Extent is similar in concept to Oracle Spatial/Locator's SDO_AGGR_MBR

Synopsis
box2d ST_Extent(geometry set geomfield);

Examples
SELECT ST_Extent(the_geom) as bextent FROM sometable;

--Return extent of each category of geometries
SELECT ST_Extent(the_geom) as bextent
FROM sometable
GROUP BY category ORDER BY category; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_3DExtent':
            self.label_17.setText("""ST_3DExtent

Description
ST_3DExtent returns a box3d (includes Z coordinate) bounding box that encloses a set of geometries. The ST_3DExtent function is an "aggregate" function in the terminology of SQL. That means that it operates on lists of data, in the same way the SUM() and AVG() functions do. Since it returns a bounding box, the spatial Units are in the units of the spatial reference system in use denoted by the SRID.

Synopsis
box3d ST_3DExtent(geometry set geomfield);

Examples
SELECT ST_3DExtent(foo.the_geom) As b3extent
FROM (SELECT ST_MakePoint(x,y,z) As the_geom
FROM generate_series(1,3) As x
CROSS JOIN generate_series(1,2) As y
CROSS JOIN generate_series(0,2) As Z) As foo; """)

        elif self.treeWidget.currentItem().text(0) == 'Find_SRID':
            self.label_17.setText("""Find_SRID

Description
The syntax is find_srid(<db/schema>, <table>, <column>) and the function returns the integer SRID of the specified column by searching through the GEOMETRY_COLUMNS table. If the geometry column has not been properly added with the AddGeometryColumns() function, this function will not work either.

Synopsis
integer Find_SRID(varchar a_schema_name, varchar a_table_name, varchar a_geomfield_name);

Examples
SELECT Find_SRID('public', 'tiger_us_state_2007', 'the_geom_4269');   

See Also --> ST_SRID  """)

        elif self.treeWidget.currentItem().text(0) == 'ST_MemSize':
            self.label_17.setText("""ST_MemSize

Description
Returns the amount of space (in bytes) the geometry takes. This is a nice compliment to PostgreSQL built in functions pg_column_size, pg_size_pretty, pg_relation_size, pg_total_relation_size.

Synopsis
integer ST_MemSize(geometry geomA);

Examples
--Return how much byte space Boston takes up in our Mass data set
SELECT pg_size_pretty(SUM(ST_MemSize(the_geom))) as totgeomsum,
pg_size_pretty(SUM(CASE WHEN town = 'BOSTON' THEN ST_MemSize(the_geom) ELSE 0 END)) As bossum,
CAST(SUM(CASE WHEN town = 'BOSTON' THEN ST_MemSize(the_geom) ELSE 0 END)*1.00 /
SUM(ST_MemSize(the_geom))*100 As numeric(10,2)) As perbos
FROM towns; """)

        elif self.treeWidget.currentItem().text(0) == 'ST_PointInsideCircle':
            self.label_17.setText("""ST_PointInsideCircle

Description
The syntax for this functions is ST_PointInsideCircle(<geometry>,<circle_center_x>,<circle_center_y>,<radius>). Returns the true if the geometry is a point and is inside the circle. Returns false otherwise.

Synopsis
boolean ST_PointInsideCircle(geometry a_point, float center_x, float center_y, float radius);

Examples
SELECT ST_PointInsideCircle(ST_Point(1,2), 0.5, 2, 3); """)

        elif self.treeWidget.currentItem().text(0) == 'PostGIS_AddBBox':
            self.label_17.setText("""PostGIS_AddBBox

Description
Add bounding box to the geometry. This would make bounding box based queries faster, but will increase the size of the geometry.

Synopsis
geometry PostGIS_AddBBox(geometry geomA);

Examples
UPDATE sometable
SET the_geom = PostGIS_AddBBox(the_geom)
WHERE PostGIS_HasBBox(the_geom) = false; """)

        elif self.treeWidget.currentItem().text(0) == 'PostGIS_DropBBox':
            self.label_17.setText("""PostGIS_DropBBox
            
Description
Drop the bounding box cache from the geometry. This reduces geometry size, but makes bounding-box based queries slower. It is also used to drop a corrupt bounding box. A tale-tell sign of a corrupt cached bounding box is when your ST_Intersects and other relation queries leave out geometries that rightfully should return true.            
            
Synopsis
geometry PostGIS_DropBBox(geometry geomA);

Examples
--This example drops bounding boxes where the cached box is not correct
--The force to ST_AsBinary before applying Box2D forces a recalculation of the box, and Box2D applied to the table geometry always
-- returns the cached bounding box.

UPDATE sometable
SET the_geom = PostGIS_DropBBox(the_geom)
WHERE Not (Box2D(ST_AsBinary(the_geom)) = Box2D(the_geom));

UPDATE sometable
SET the_geom = PostGIS_AddBBox(the_geom)
WHERE Not PostGIS_HasBBOX(the_geom);       """)
            
        elif self.treeWidget.currentItem().text(0) == 'PostGIS_HasBBox':
            self.label_17.setText("""PostGIS_HasBBox
            
Description
Returns TRUE if the bbox of this geometry is cached, FALSE otherwise. Use PostGIS_AddBBox and PostGIS_DropBBox to control caching.            
            
Synopsis
boolean PostGIS_HasBBox(geometry geomA);            
            
Examples
SELECT the_geom
FROM sometable WHERE PostGIS_HasBBox(the_geom) = false; """)              

        else:
            pass
        