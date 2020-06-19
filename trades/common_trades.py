import pandas as pd
from dateutil.parser import parse

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

parse_dates = ['Contract_Month', 'Trade_Date', 'Delivery_Month']


def logic(file_path):
    input_data = pd.read_csv(
        file_path,
        names=input_data_col_names,
        header=0
    ).dropna(subset=['Client_info'])

    input_data = input_data.fillna(0)

    for attr in parse_dates:
        input_data[attr] = input_data[attr].apply(parse)

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
        #    'Remarks',
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
    lme_prices = getLmePrices(preout['ticker'][preout['Traded_Price'] == 0])
    preout = preout.merge(lme_prices, how='left', on='ticker').drop_duplicates().reset_index()
    # Extra fee for carry trades
    preout['Traded_Price'][(preout['Traded_Price'] == 0) & (preout['Buy_Sell'] == 'B')] = preout['value'] + preout[
        'Comm']
    preout['Traded_Price'][(preout['Traded_Price'] == 0) & (preout['Buy_Sell'] == 'S')] = preout['value'] - preout[
        'Comm']

    preout = preout.drop(list(lme_prices.columns), axis=1)

    preout['BuyRate'] = preout['Traded_Price']
    preout['SellRate'] = preout['Traded_Price']
    preout['BuyPrice'] = preout['Traded_Price'] * preout['Traded_Qty']
    preout['SellPrice'] = preout['Traded_Price'] * preout['Traded_Qty']

    preout['Contract_Month'] = preout['Contract_Month'].astype(str)
    preout['Delivery_Month'] = preout['Delivery_Month'].astype(str)
    preout['LastTradeingDate'] = None
    preout['Comm'] = 0
    preout = preout[selected_cols].rename(columns=rename_map)

    preout = preout[preout['CurrPrice'].notnull()]

    # Send data to ZeroLayer CommodityTradesTemp
    cursor = getCursor(driver, server, database_js, username, password)
    cursor.execute("TRUNCATE TABLE dbo.CommodityTradesTemp")
    preout.to_sql('CommodityTradesTemp', engine_js, index=False, if_exists="append", schema="dbo")

    # Exec SP
    cursor.execute("exec CommodityContractMasterAndTradesUpload_CommonFile 'aarna'")
    rc = cursor.fetchall()
    rc = [x[0] for x in rc]
    cursor.close()
    return rc


def main():
    return logic()


if __name__ == "__main__":
    main()
