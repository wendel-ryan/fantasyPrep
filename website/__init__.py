from flask import Flask
import sqlite3
from os import path

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'ryans_secretkey'

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app

