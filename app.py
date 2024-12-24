from flask import Flask, redirect, url_for, render_template, send_from_directory, request
import os
from os import path
from back import back

from flask_sqlalchemy import SQLAlchemy
from db import db
from db.models import Users

from flask_login import LoginManager
login_manager = LoginManager()
login_manager.login_view = 'back.login'


app = Flask(__name__)

login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY ', 'несекретно-секретный секрет')
app.config['DB_TYPE'] = os.getenv('DB_TYPE', 'sqlite')

if app.config['DB_TYPE'] == 'postgres':
    db_name = 'pavel_krasov_sw'
    db_user = 'pavel_krasov_sw'
    db_password = '777'
    host_ip = '127.0.0.1'
    host_port = '5432'

    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{host_ip}:{host_port}/{db_name}'
else:
    dir_path = path.dirname(path.realpath(__file__))
    db_path = path.join(dir_path, "pavel_krasov_sw.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

db.init_app(app)

app.register_blueprint(back)


# функция, которая обрабатывает отдачу
# статики из корневой директории сайта
@app.route('/favicon.ico')
@app.route('/sitemap.xml')
@app.route('/robots.txt')
def static_root():
    return send_from_directory(app.static_folder, request.path[1:])