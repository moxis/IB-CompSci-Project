import os
from flask import Flask, render_template, flash, request, url_for, redirect, Markup
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import basedir

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import views, models
