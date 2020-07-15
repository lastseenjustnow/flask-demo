import urllib
import sqlalchemy
from sqlalchemy import event
import pyodbc


def getEngine(dr, s, db, u, p):
    params = 'DRIVER=' + dr + ';SERVER=' + s + \
        ';PORT=1433;DATABASE=' + db + ';UID=' + u + ';PWD=' + p
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


def getCursor(dr, s, db, u, p):
    params = 'DRIVER=' + dr + ';SERVER=' + s + \
        ';PORT=1433;DATABASE=' + db + ';UID=' + u + ';PWD=' + p
    return pyodbc.connect(params, autocommit=True).cursor()


# Server config-200
server = '192.168.1.200'
username = 'deepika'
password = '7exGnjkof493'
driver = '{ODBC Driver 17 for SQL Server}'

# Engines
database_js = 'Jsoham'
engine_js = getEngine(driver, server, database_js, username, password)

database_frx = 'JsohamFRX'
engine_frx = getEngine(driver, server, database_frx, username, password)

database_zl = 'ZeroLayer'
engine_zl = getEngine(driver, server, database_zl, username, password)

database_aarna = 'AarnaProcess'
engine_aarna = getEngine(driver, server, database_aarna, username, password)

# Added new database config
database_dt = 'DropCopyTrade'
engine_aarna = getEngine(driver, server, database_aarna, username, password)
