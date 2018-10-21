from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

app = Flask(__name__)
app.config.from_object("config")

app.cache = Cache(app, config={"CACHE_TYPE": "simple"})

db = SQLAlchemy(app)

from app import views, models
