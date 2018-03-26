from flask import Flask
import flask_excel

app = Flask(__name__)
flask_excel.init_excel(app)

from web_ui import routes
