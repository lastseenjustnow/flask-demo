from flask import Flask, render_template
from flask_table import Table, Col


class ResultsTable(Table):
  info = Col('Info')

class ResultInfo(object):
  def __init__(self, info):
    self.info = info


app = Flask(__name__)


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/results/')
def results():
  import trades.run as logic
  res = ResultsTable([ResultInfo(x) for x in logic.main()])
  return render_template('results.html', table=res)


if __name__ == '__main__':
  app.run(debug=True, host='192.168.1.108')