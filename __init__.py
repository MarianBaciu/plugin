
def classFactory(iface):

    from .DBPlugin import DBPlugin
    return DBPlugin(iface) #DBPLugin ist unsere Hauptklasse
