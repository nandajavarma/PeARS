#!/usr/bin/env python

from flask import Flask, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy
import os


app = Flask(__name__)
db = SQLAlchemy(app)
app.config.from_object('config')



from pears import models, searcher, indexer, api, scorePages

app.register_blueprint(searcher.searcher)
app.register_blueprint(indexer.indexer)
app.register_blueprint(api.api)
