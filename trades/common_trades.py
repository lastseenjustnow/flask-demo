import pandas as pd
import numpy as np
import re

import pdblp

from trades.odbc import *


def getLmePrices(ser: pd.Series):
    if ser.empty:
        return pd.DataFrame(columns=['ticker', 'value'])
    con = pdblp.BCon(debug=True, host='192.168.1.142', port=6969, timeout=5000)
    con.start()
    data = con.ref(list(ser), 'PX_SETTLE')
    con.stop()
    return data


# input_data

database = database_js
engine = engine_js

input_data_col_names = [
    'Client_info',
    'Com_Type',
    'Exch_code',
    'Com_code',
    'Contract_Month',
    'Strike_Price',
    'Call_Put',
    'Trade_Date',
    'Buy_Sell',
    'Traded_Qty',
    'Traded_Price',
    'Curr_Code',
    'Order_Id',
    'Trade_Source',
    'MCP',
    'Comm',
    'Remarks',
    'Delivery_Month',
    'Trade_Time'
]


def logic(file_path):
    input_data = pd.read_csv(
        file_path,
        names=input_data_col_names,
        header=0
    ).dropna(subset=['Client_info'])

    input_data[['Strike_Price', 'Call_Put']] = input_data[['Strike_Price', 'Call_Put']].fillna(0)
    input_data['Traded_Price'] = input_data['Traded_Price'].fillna(-1)

    parse_dates = ['Contract_Month', 'Trade_Date', 'Delivery_Month']

    # Raise exception when dates do no comply with predefined formats
    regexp = re.compile('(\d{2})(?P<s>[/.-])(\d{2})(?P=s)(\d{4})$')
    bools = input_data[parse_dates].applymap(lambda x: bool(regexp.match(x)))
    bools.index = bools.index + 1
    incorrect_values = np.array(bools[bools == False].stack().index)
    if len(incorrect_values):
        message_text_func = np.vectorize(lambda x: "Row number is: {}, column: {}".format(x[0], x[1]))
        messages = message_text_func(incorrect_values)
        return np.append(
            np.insert(messages, 0, "We could not parse dates over specified locations:"),
            "Please, specify dates in following formats: 'dd/mm/yyyy', 'dd-mm-yyyy', 'dd.mm.yyyy'"
        )

    # Parse dates with predefined explicitly stated formats
    slash = input_data[parse_dates].apply(pd.to_datetime, format='%d/%m/%Y', errors='coerce')
    underscore = input_data[parse_dates].apply(pd.to_datetime, format='%d-%m-%Y', errors='coerce')
    dot = input_data[parse_dates].apply(pd.to_datetime, format='%d.%m.%Y', errors='coerce')
    input_data[parse_dates] = slash.combine_first(underscore).combine_first(dot)

    # Remove redundant spaces at the beginning & the end of each string value
    strs = input_data.select_dtypes(['object'])
    input_data[strs.columns] = input_data[strs.columns].apply(lambda x: x.astype(str).str.strip())
    input_data["Client_info"] = input_data["Client_info"].apply(lambda x: x.replace(" ", ""))

    # master entities
    client_master = pd.read_sql_table("ClientMaster", engine_js)
    security_master_t1 = pd.read_sql_table("SecurityMasterT1", engine_js)

    # contract_code_absence! add exception
    codes = ["PHILLIP_CODE", "RJ_CONTRACT_CODE", "CQG_CODE", "SecurityCode"]
    contract_code_absence = pd.concat(
        [input_data.merge(security_master_t1, how="left", left_on="Com_code", right_on=code) for code in codes]
    )

    contract_code_absence["is_code_absense"] = contract_code_absence[codes].isnull().all(axis=1).astype(int)
    contract_code_absence = contract_code_absence \
        .assign(
        code_absence=contract_code_absence.groupby(contract_code_absence.index)['is_code_absense'].sum()
    )
    contract_code_absence = contract_code_absence.loc[~contract_code_absence.index.duplicated(keep='first')]
    contract_code_absence[contract_code_absence.code_absence == 4]['Com_code'].drop_duplicates()

    # importfilest2

    selected_cols = [
        'ClientCode',
        'Curr_Code',
        'Com_code',
        'Com_Type',
        'OptType',
        'Trade_Date',
        'Contract_Month',
        'Buy_Sell',
        'Traded_Qty',
        'Traded_Price',
        'BuyRate',
        'SellRate',
        'Margin',
        'MCP',
        'Comm',
        'Fees',
        'BuyDealId',
        'SellDealId',
        'TickValue',
        'TickSize',
        'Exch_code',
        'Delivery_Month',
        #    'CPCode',
        'TradeID',
        #    'UTC',
        'Strike_Price',
        #    'Traded_Premium',
        #    'Option_Premium',
        #    'Client_Reference',
        'Remarks',
        'Trade_Time',
        'Trade_Source',
        'LastTradeingDate'
    ]

    rename_map = {
        "Curr_Code": "CurrencyCode",
        "Com_code": "Ticker",
        "Com_Type": "CmdType",
        "Trade_Date": "TradeDate",
        "Contract_Month": "ExpiryDate",
        "Buy_Sell": "BuySellFlag",
        'Traded_Qty': "Qty",
        'Traded_Price': "CurrPrice",
        'MCP': "MCPCode",
        'Comm': "Commission",
        'Delivery_Month': "DelMonth",
        'Exch_code': "MarketCode",
        'Strike_Price': "StrikePrice",
        'Trade_Time': 'TradeTime',
        'Trade_Source': 'TradeSource'
    }

    def opt_type_func(x): return '' if x['Com_Type'] == 'F' else x['Call_Put']

    preout = contract_code_absence[contract_code_absence[codes].notnull().any(axis=1)] \
        .drop_duplicates().merge(client_master, how="left", left_on="Client_info", right_on="ClientCode")
    preout = preout.assign(OptType=preout.apply(opt_type_func, axis=1).fillna(''))
    preout['Margin'] = '0.00'
    preout['Comm'] = preout['Comm'].astype(float).fillna(0.0)
    preout['Fees'] = '0.00'
    preout['BuyDealId'] = preout['Order_Id']
    preout['SellDealId'] = preout['Order_Id']
    preout['TickSize'] = 1
    # preout['CPCode']=preout['MCP']
    preout['TradeID'] = preout['Order_Id']
    # preout['UTC']=''
    # preout['Traded_Premium']=preout['Traded_Price']
    # preout['Option_Premium']=preout['Traded_Price']
    # preout['Client_Reference']=preout['Client_info']

    preout['Trade_Date'] = preout['Trade_Date'].astype(str)

    preout['ticker'] = 'LM' + preout['Com_code'] + 'P ' + preout['Contract_Month'].dt.strftime("%Y%m%d") + ' LME Comdty'
    lme_prices = getLmePrices(preout['ticker'][preout['Traded_Price'] == -1])
    preout = preout.merge(lme_prices, how='left', on='ticker').drop_duplicates().reset_index()
    # Extra fee for carry trades
    preout['Traded_Price'][(preout['Traded_Price'] == -1) & (preout['Buy_Sell'] == 'B')] = preout['value'] + preout[
        'Comm']
    preout['Traded_Price'][(preout['Traded_Price'] == -1) & (preout['Buy_Sell'] == 'S')] = preout['value'] - preout[
        'Comm']

    preout = preout.drop(list(lme_prices.columns), axis=1)

    preout['BuyRate'] = preout['Traded_Price']
    preout['SellRate'] = preout['Traded_Price']
    preout['BuyPrice'] = preout['Traded_Price'] * preout['Traded_Qty']
    preout['SellPrice'] = preout['Traded_Price'] * preout['Traded_Qty']

    preout['Contract_Month'] = preout['Contract_Month'].astype(str)
    preout['Delivery_Month'] = preout['Delivery_Month'].dt.strftime("%b-%y").str.upper().astype(str)
    preout['LastTradeingDate'] = None
    preout['Comm'] = 0
    preout = preout[selected_cols].rename(columns=rename_map)

    missing_prices_count = len(preout[preout['CurrPrice'].isnull()])
    preout = preout[preout['CurrPrice'].notnull()].drop_duplicates()

    # Send data to ZeroLayer CommodityTradesTemp
    cursor = getCursor(vlad_201, database)
    cursor.execute("TRUNCATE TABLE dbo.CommodityTradesTemp")
    preout.to_sql('CommodityTradesTemp', engine, index=False, if_exists="append", schema="dbo")

    # Exec SP
    cursor.execute("exec CommodityContractMasterAndTradesUpload_CommonFile 'aarna'")
    rc = cursor.fetchall()
    rc = [x[0] for x in rc]
    rc.insert(0, "Database updated: {}".format(database))
    rc.append("BBG prices missing for contracts number: {}".format(missing_prices_count))
    cursor.close()
    return rc
