#!/usr/bin/env python

from flask import Flask, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
db = SQLAlchemy(app)
app.config.from_object('config')

from dht.entangled.node import EntangledNode
from dht.entangled.kademlia.datastore import SQLiteDataStore
if os.path.isfile('/tmp/dbFile%s.db' % 4000):
    os.remove('/tmp/dbFile%s.db' % 4000)
data_store = SQLiteDataStore(dbFile = '/tmp/db_file_dht%s.db' % 4000)
node = EntangledNode(udpPort=int(4000), dataStore=data_store)

from pears import models, searcher, indexer, api

app.register_blueprint(searcher.searcher)
app.register_blueprint(indexer.indexer)
app.register_blueprint(api.api)
