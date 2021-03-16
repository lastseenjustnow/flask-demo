import urllib
import sqlalchemy
from sqlalchemy import event
import pyodbc


class MicrosoftServer:
    def __init__(self, server, username, password):
        self.server = server
        self.username = username
        self.password = password
        self.driver = '{ODBC Driver 17 for SQL Server}'


def getCursor(ms: MicrosoftServer, db):
    params = 'DRIVER=' + ms.driver + ';SERVER=' + ms.server + \
             ';PORT=1433;DATABASE=' + db + ';UID=' + ms.username + ';PWD=' + ms.password
    return pyodbc.connect(params, autocommit=True).cursor()


def getEngine(ms: MicrosoftServer, db):
    params = 'DRIVER=' + ms.driver + ';SERVER=' + ms.server + \
        ';PORT=1433;DATABASE=' + db + ';UID=' + ms.username + ';PWD=' + ms.password
    db_params = urllib.parse.quote_plus(params)
    engine = sqlalchemy.create_engine(
        "mssql+pyodbc:///?odbc_connect={}".format(db_params), pool_pre_ping=True)

    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(
            conn, cursor, statement, params, context, executemany
    ):
        if executemany:
            cursor.fast_executemany = True
    return engine


vlad_201 = MicrosoftServer('192.168.1.201', 'vlad', 'Kapusta2020')
vlad_137 = MicrosoftServer('192.168.1.137', 'vlad', 'Kapusta2025')
deepika_200 = MicrosoftServer('192.168.1.200', 'vlad', 'Kapusta2020')
deepika_201 = MicrosoftServer('192.168.1.201', 'vlad', 'Kapusta2020')

# Engines
database_js = 'Jsoham'
engine_js = getEngine(vlad_201, database_js)

database_frx = 'JsohamFRX'
engine_frx = getEngine(vlad_201, database_frx)

database_zl = 'ZeroLayer'
engine_zl = getEngine(vlad_201, database_zl)

database_aarna = 'AarnaProcess'
engine_aarna = getEngine(vlad_201, database_aarna)

database_backoffice = 'backoffice'
engine_backoffice = getEngine(vlad_137, database_aarna)

# Added new database config
database_cme = 'DropCopyTrade'
engine_cme = getEngine(deepika_200, database_cme)

database_cqg = 'CQGDropCopyInhouse'
engine_cqg = getEngine(deepika_200, database_cqg)

database_tt = 'DropCopyDataBase'
engine_tt = getEngine(deepika_200, database_tt)

database_jsoham = 'JSOHAM'
engine_jsoham = getEngine(deepika_201, database_jsoham)
