import pandas as pd

import pdblp

from trades.odbc import *


def getSecPrices(df: pd.DataFrame):
    con = pdblp.BCon(debug=True, host='192.168.1.142', port=6969, timeout=5000)
    con.start()
    data = pd.concat([con.ref(list(df['BloombergCode'][df['field'] == field]), field) for field in df.field.unique()])
    con.stop()
    return data


def logic(date):
    result = pd.read_sql_query("exec SP_SettlementPriceBloombergTickers '{}'".format(date), engine_aarna)

    # TODO: Handle FX prices!!!
    result = result[result['BloombergCode'].str.split().apply(len) > 1]

    result['BloombergCode'] = result['BloombergCode'].str.rsplit(' ', 1).apply(lambda x: x[0].upper() + ' ' + x[1])
    prices = getSecPrices(result)
    settle_price = result.merge(prices, how='inner', left_on='BloombergCode', right_on='ticker').drop_duplicates()[['SecurityCode', 'value', 'Date']]

    rename_map = {
        "SecurityCode": "securitycode",
        "value": "price",
        "Date": "Sdate"
    }

    settle_price = settle_price.rename(columns=rename_map)
    settle_price = settle_price[settle_price['price'].notnull()]

    cursor_aarna = getCursor(driver, server, database_aarna, username, password)
    cursor_aarna.execute("TRUNCATE TABLE SettlementPriceTemp")
    cursor_aarna.close()

    settle_price.to_sql('SettlementPriceTemp', engine_aarna, index=False, if_exists="append", schema="dbo")

    # TODO: database change for FRX
    cursor = getCursor(driver, server, database_aarna, username, password)
    cursor.execute("exec ImportSettlementPrice_Vlad '{}'".format(date))
    rc = cursor.fetchall()
    rc = [x[0] for x in rc]
    cursor.close()
    return rc
