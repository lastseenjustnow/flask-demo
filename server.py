from flask import Flask, render_template
from flask_table import Table, Col

import os
from flask import request, flash, redirect
from werkzeug.utils import secure_filename
from werkzeug.middleware.shared_data import SharedDataMiddleware

from trades import common_trades
from trades import security_prices


class ResultsTable(Table):
    info = Col('Info')


class ResultInfo(object):
    def __init__(self, info):
        self.info = info


app = Flask(__name__)

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
            res = ResultsTable([ResultInfo(x) for x in common_trades.logic(filepath)])
            return render_template('results.html', table=res)
    return render_template('index.html')


@app.route('/generate_prices', methods=['GET', 'POST'])
def generate_prices():
    res = ResultsTable([ResultInfo(x) for x in security_prices.logic(request.form['File Date'])])
    return render_template('results.html', table=res)


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.run(debug=True, host='192.168.1.108')
