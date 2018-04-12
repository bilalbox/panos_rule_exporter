from flask import Flask
import flask_excel

app = Flask(__name__)
app.secret_key = 'my super secret key'
app.config['UPLOAD_FOLDER'] = '/home/panos/configs/'
flask_excel.init_excel(app)

from web_ui import routes
