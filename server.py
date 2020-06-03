from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/my-link/')
def my_link():
  app.logger.info(' failed to log in')
  import trades.run
  return 'File is uploaded'

if __name__ == '__main__':
  app.run(debug=True)