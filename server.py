from flask import Flask, render_template
from flask_table import Table, Col
from flask_cors import CORS

import os
from flask import request, flash, redirect, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.shared_data import SharedDataMiddleware

from trades import common_trades
from trades import security_prices
from trades.odbc import *
import json
import collections
import ssl
import datetime
import decimal
import requests


class ResultsTable(Table):
    info = Col('Info')


class ResultInfo(object):
    def __init__(self, info):
        self.info = info


app = Flask(__name__)
cors = CORS(app)
UPLOAD_FOLDER = r'C:\\Users\\Vlad\\uploads\\'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app.add_url_rule('/uploads/<filename>',
                 'uploaded_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/uploads': app.config['UPLOAD_FOLDER']
})


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = UPLOAD_FOLDER + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            res = ResultsTable([ResultInfo(x)
                                for x in common_trades.logic(filepath)])
            return render_template('results.html', table=res)
    return render_template('index.html')


@app.route('/cme', methods=['GET'])
def getCMEDropCopy():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(deepika_200, database_cme)
    rows = cursor_aarna.execute(
        "select * from DropCopyTrade..DropCopyTrade where tradedate like'%" + date + "%';").fetchall()
    columns = [],
    items = [],

    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], row))
             for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/cqg', methods=['GET'])
def getCQGDropCopy():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(deepika_200, database_cqg)
    rows = cursor_aarna.execute(
        "select * from CQGDropCopyInhouse..TradePos where ctransacttime like '%" + date + "%';").fetchall()
    columns = [],
    items = [],

    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], row))
             for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/tt', methods=['GET'])
def getTTDropCopy():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(deepika_200, database_tt)
    rows = cursor_aarna.execute(
        "select * from DropCopyDataBase..DropCopyTable_Inhouse where ordstatus in ('Filled','PartialFilled') and transacttime like '%" + date + "%';").fetchall()
    columns = [],
    items = [],

    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], row))
             for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/fcpositions', methods=['GET'])
def getFCPosition():
    date = request.args.get('date')
    contract = request.args.get('contractcode')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from FCSTONEPosition where pfc ='"+contract+"'and  recdate='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/EDFUKPosition', methods=['GET'])
def getEDFUKPosition():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from EDFUKPosition where recdate='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/EDFUSPosition', methods=['GET'])
def getEDFUSPosition():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from EDFUSPosition where recdate='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/Philipposition', methods=['GET'])
def getPhilipposition():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from Philipposition where recdate='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/AdvantagePosition', methods=['GET'])
def getAdvantagePosition():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from AdvantagePosition where recdate='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/fcbalances', methods=['GET'])
def getFCBalances():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from FcstoneBalances  where InsertingDate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/EDFUkBalances', methods=['GET'])
def getEDFUKBalances():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from EDFUkBalances where InsertingDate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/EDFUsBalances', methods=['GET'])
def getEDFUsBalances():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from EDFUSBalances where InsertingDate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/KgieFutureandFXBalances', methods=['GET'])
def getKgieFutureandFXBalances():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from KgieFutureandFXBalances where InsertingDate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/PhilipBalances', methods=['GET'])
def getPhilipBalances():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from PhilipBalances  where InsertingDate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/MayBankBalances', methods=['GET'])
def getMayBankBalances():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from MayBankBalances  where InsertingDate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/fcsettlements', methods=['GET'])
def getfcsettlements():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from GetFCESettlement  where recdate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/EDfUSSettlement', methods=['GET'])
def getEefUSSettlement():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from GetEefUSSettlement where recdate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/EDFUKSettlement', methods=['GET'])
def getEDFUKSettlement():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from GetEDFUKSettlement where recdate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/philipsettlement', methods=['GET'])
def getphilipsettlement():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from getphilipsettlement where recdate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/AdvantageTrades', methods=['GET'])
def getAdvantageTrades():
    date = request.args.get('date')
    print(date)
    cursor_aarna = getCursor(vlad_201, database_aarna)
    rows = cursor_aarna.execute(
        "select * from AdvantageTrades  where recdate ='" + date + "'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.date):
            return str(x)
        return (x)
    columns = [],
    items = [],
    columns = [key[0] for key in cursor_aarna.description]
    items = [dict(zip([key[0] for key in cursor_aarna.description], [
        to_datetime(x) for x in row])) for row in rows]
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/openPositions', methods=['GET'])
def getOpenPosition():
    cursor = getCursor(deepika_201, database_jsoham)
    date = request.args.get('date')
    rows = cursor.execute(
        "EXEC OpenPositionsCMD_DAS '" + date + "' ,'0','zz','0','zzz','0','ZZ','0','ZZ','0','ZZ','AARNA'").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.datetime):
            return (x.strftime("%Y-%m-%d"))
        if isinstance(x, decimal.Decimal):
            return str(x)
        return (x)

    columns = [],
    items = [],
    columns = [key[0] for key in cursor.description]
    items = [dict(zip([key[0] for key in cursor.description], [
        to_datetime(x) for x in row])) for row in rows]
    # print(rows)
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/tradeDetails', methods=['GET'])
def getTradeDetails():
    cursor = getCursor(deepika_201, database_jsoham)
    fromDate = request.args.get('fromDate')
    toDate = request.args.get('toDate')
    if request.args.get('otherCode') == 'null':
        otherCode = 'IS NOT NULL'
    elif request.args.get('otherCode'):
        otherCode = 'like' + "'%" + request.args.get('otherCode') + "%'"
    if request.args.get('clientCode') == 'null':
        clientCode = 'IS NOT NULL'
    elif request.args.get('clientCode'):
        clientCode = 'like' + "'%" + request.args.get('clientCode') + "%'"

    if request.args.get('securityCode') == 'null':
        securityCode = 'IS NOT NULL'
    elif request.args.get('securityCode'):
        securityCode = ' = ' + request.args.get('securityCode')

    print(clientCode)
    print(securityCode)
    print(otherCode)

    rows = cursor.execute(
        "SELECT T1.SecurityCode as ContractCode, S.securityname, (T.MktValue/(S.MarketLot*T.QTY)) AS TradePrice,S.securityCode, * FROM jsoham..TRADES T INNER JOIN jsoham..SECURITYMASTER S ON T.SecurityCode=S.SecurityCode INNER JOIN JSOHAM..SECURITYMASTERT1 T1 ON S.TICKER=T1.SecurityCode WHERE T.tradedate between '" +
        fromDate + "' and '" + toDate + "' and T.othercode " + otherCode + " and T.clientcode " + clientCode + " and T.securitycode " + securityCode + " ").fetchall()

    def to_datetime(x):
        if isinstance(x, datetime.datetime):
            return (x.strftime("%Y-%m-%d"))
        if isinstance(x, decimal.Decimal):
            return str(x)
        return (x)

    columns = [],
    items = [],
    columns = [key[0] for key in cursor.description]
    items = [dict(zip([key[0] for key in cursor.description], [
        to_datetime(x) for x in row])) for row in rows]
    # print(rows)
    j = json.dumps({'items': items, 'columns': columns})
    return jsonify(j)


@app.route('/generate_prices', methods=['GET', 'POST'])
def generate_prices():
    res = ResultsTable([ResultInfo(x)
                        for x in security_prices.logic(request.form['File Date'])])
    return render_template('results.html', table=res)


@app.route('/generate_bond_parameters', methods=['GET', 'POST'])
def generate_bond_parameters():
    data = {"conf": {"to_date": request.form['bond_param_date']}}
    requests.post(
        "http://localhost:8080/api/experimental/dags/bbg_bonds/dag_runs", data=json.dumps(data))
    res = ResultsTable([ResultInfo("Request to Bloomberg has been sent.")])
    return render_template('results.html', table=res)


@app.route('/reco_fcstone_trade_price_trnfhr', methods=['GET', 'POST'])
def reco_fcstone_trade_price_trnfhr():
    data = {"conf": {"to_date": request.form['fcst_trade_price_trnfhr']}}
    requests.post("http://localhost:8080/api/experimental/dags/fcstone_trnfhr/dag_runs",
                  data=json.dumps(data))
    res = ResultsTable(
        [ResultInfo("Command has been passed to a server. File will have been delivered to email in a few minutes.")])
    return render_template('results.html', table=res)


@app.route('/reco_fcstone_trade_price_st4f1', methods=['GET', 'POST'])
def reco_fcstone_trade_price_st4f1():
    data = {"conf": {"to_date": request.form['fcst_trade_price_st4f1']}}
    requests.post("http://localhost:8080/api/experimental/dags/fcstone_st4f1/dag_runs",
                  data=json.dumps(data))
    res = ResultsTable(
        [ResultInfo("Command has been passed to a server. File will have been delivered to email in a few minutes.")])
    return render_template('results.html', table=res)


@app.route('/reco_fcstone_settlement_prices', methods=['GET', 'POST'])
def reco_fcstone_settlement_prices():
    data = {"conf": {"to_date": request.form['fcst_settl_prices']}}
    requests.post("http://localhost:8080/api/experimental/dags/reco_fcstone_settlement_prices/dag_runs",
                  data=json.dumps(data))
    res = ResultsTable(
        [ResultInfo("Command has been passed to a server. File will have been delivered to email in a few minutes.")])
    return render_template('results.html', table=res)

@app.route('/kgi_trade_price', methods=['GET', 'POST'])
def reco_kgi_trade_price():
    data = {"conf": {"to_date": request.form['kgi_trade_price']}}
    requests.post("http://localhost:8080/api/experimental/dags/kgi_trade_price/dag_runs",
                  data=json.dumps(data))
    res = ResultsTable(
        [ResultInfo("Command has been passed to a server. File will have been delivered to email in a few minutes.")])
    return render_template('results.html', table=res)

@app.route('/reco_client_broker', methods=['GET', 'POST'])
def reco_client_broker():
    data = {"conf": {"to_date": request.form['reco_client_broker']}}
    requests.post("http://localhost:8080/api/experimental/dags/reco_client_broker/dag_runs",
                  data=json.dumps(data))
    res = ResultsTable(
        [ResultInfo("Command has been passed to a server. File will have been delivered to email in a few minutes.")])
    return render_template('results.html', table=res)


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True, host='192.168.1.183',
            ssl_context='adhoc')
