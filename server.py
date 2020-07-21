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


@ app.route('/generate_prices', methods=['GET', 'POST'])
def generate_prices():
    res = ResultsTable([ResultInfo(x)
                        for x in security_prices.logic(request.form['File Date'])])
    return render_template('results.html', table=res)


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True, host='192.168.1.111',
            ssl_context='adhoc')
