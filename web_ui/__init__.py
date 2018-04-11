from flask import Flask
from flask_bootstrap import Bootstrap
import flask_excel

app = Flask(__name__)
flask_excel.init_excel(app)
Bootstrap(app)

from web_ui import routes
