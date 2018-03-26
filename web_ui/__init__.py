from flask import Flask

app = Flask(__name__)

from web_ui import routes
