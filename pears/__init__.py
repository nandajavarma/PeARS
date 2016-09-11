#!/usr/bin/env python

from flask import Flask, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from pears import models, searcher, indexer

app.register_blueprint(searcher.searcher)
app.register_blueprint(indexer.indexer)
