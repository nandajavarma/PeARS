#!/usr/bin/env python
#
# This library is free software, distributed under the terms of
# the GNU Lesser General Public License Version 3, or any later version.
# See the COPYING file included in this archive
#
# The docstrings in this module contain epytext markup; API documentation
# may be created by processing this file with epydoc: http://epydoc.sf.net

import UserDict
import sqlite3
import cPickle as pickle
import time
import os
from pears import db
from pears.models import DhtData



class DataStore(UserDict.DictMixin):
    """ Interface for classes implementing physical storage (for data
    published via the "STORE" RPC) for the Kademlia DHT

    @note: This provides an interface for a dict-like object
    """
    def keys(self):
        """ Return a list of the keys in this data store """

    def lastPublished(self, key):
        """ Get the time the C{(key, value)} pair identified by C{key}
        was last published """

    def originalPublisherID(self, key):
        """ Get the original publisher of the data's node ID

        @param key: The key that identifies the stored data
        @type key: str

        @return: Return the node ID of the original publisher of the
        C{(key, value)} pair identified by C{key}.
        """

    def originalPublishTime(self, key):
        """ Get the time the C{(key, value)} pair identified by C{key}
        was originally published """

    def setItem(self, key, value, lastPublished, originallyPublished, originalPublisherID):
        """ Set the value of the (key, value) pair identified by C{key};
        this should set the "last published" value for the (key, value)
        pair to the current time
        """

    def __getitem__(self, key):
        """ Get the value identified by C{key} """

    def __setitem__(self, key, value):
        """ Convenience wrapper to C{setItem}; this accepts a tuple in the
        format: (value, lastPublished, originallyPublished, originalPublisherID) """
        self.setItem(key, *value)

    def __delitem__(self, key):
        """ Delete the specified key (and its value) """

class DictDataStore(DataStore):
    """ A datastore using an in-memory Python dictionary """
    def __init__(self):
        # Dictionary format:
        # { <key>: (<value>, <lastPublished>, <originallyPublished> <originalPublisherID>) }
        self._dict = {}

    def keys(self):
        """ Return a list of the keys in this data store """
        return self._dict.keys()

    def lastPublished(self, key):
        """ Get the time the C{(key, value)} pair identified by C{key}
        was last published """
        return self._dict[key][1]

    def originalPublisherID(self, key):
        """ Get the original publisher of the data's node ID

        @param key: The key that identifies the stored data
        @type key: str

        @return: Return the node ID of the original publisher of the
        C{(key, value)} pair identified by C{key}.
        """
        return self._dict[key][3]

    def originalPublishTime(self, key):
        """ Get the time the C{(key, value)} pair identified by C{key}
        was originally published """
        return self._dict[key][2]

    def setItem(self, key, value, lastPublished, originallyPublished, originalPublisherID):
        """ Set the value of the (key, value) pair identified by C{key};
        this should set the "last published" value for the (key, value)
        pair to the current time
        """
        self._dict[key] = (value, lastPublished, originallyPublished, originalPublisherID)

    def __getitem__(self, key):
        """ Get the value identified by C{key} """
        return self._dict[key][0]

    def __delitem__(self, key):
        """ Delete the specified key (and its value) """
        del self._dict[key]


class SQLiteDataStore(DataStore):
    """ Example of a SQLite database-based datastore
    """
    def __init__(self, dbFile=':memory:'):
        """
        @param dbFile: The name of the file containing the SQLite database; if
                       unspecified, an in-memory database is used.
        @type dbFile: str
        """
        self._db = db

    def keys(self):
        """ Return a list of the keys in this data store """
        keys = []
        try:
            keys = [each.key.decode('hex') for each in db.session.query(DhtData).all()]
        finally:
            return keys

    def lastPublished(self, key):
        """ Get the time the C{(key, value)} pair identified by C{key}
        was last published """
        return int(self._dbQuery(key, 'lastPublished'))
        try:
            return db.session.query(DhtData).filter_by(
                    key=key).first().lastPublished
        except:
            raise KeyError, key

    def originalPublisherID(self, key):
        """ Get the original publisher of the data's node ID

        @param key: The key that identifies the stored data
        @type key: str

        @return: Return the node ID of the original publisher of the
        C{(key, value)} pair identified by C{key}.
        """
        try:
            return db.session.query(DhtData).filter_by(
                    key=key).first().originalPublisherID
        except:
            raise KeyError, key

    def originalPublishTime(self, key):
        """ Get the time the C{(key, value)} pair identified by C{key}
        was originally published """
        try:
            return db.session.query(DhtData).filter_by(
                    key=key).first().originallyPublished
        except:
            raise KeyError, key

    def setItem(self, key, value, lastPublished, originallyPublished, originalPublisherID):
        # Encode the key so that it doesn't corrupt the database
        encodedKey = key.encode('hex')
        item_present = db.session.query(DhtData).filter_by(key=encodedkey)
        if not item_present.first():
            item = DhtData(key=encodedkey, value=value, lastPublished=lastPublished,
                    originallyPublished=originallyPublished, originalPublisherID=originalPublisherID)
            db.session.add(item)
            # self._cursor.execute('INSERT INTO data(key, value, lastPublished, originallyPublished, originalPublisherID) VALUES (?, ?, ?, ?, ?)', (encodedKey, buffer(pickle.dumps(value, pickle.HIGHEST_PROTOCOL)), lastPublished, originallyPublished, originalPublisherID))
        else:
            item_present.value = value
            item_present.lastPublished = lastPublished
            item_present.originallyPublished = originallyPublished
            item_present.originalPublisherID = originalPublisherID
        db.session.commit()
            # self._cursor.execute('UPDATE data SET value=?, lastPublished=?, originallyPublished=?, originalPublisherID=? WHERE key=?', (buffer(pickle.dumps(value, pickle.HIGHEST_PROTOCOL)), lastPublished, originallyPublished, originalPublisherID, encodedKey))

    # def _dbQuery(self, key, columnName, unpickle=False):
        # try:
            # self._cursor.execute("SELECT %s FROM data WHERE key=:reqKey" % columnName, {'reqKey': key.encode('hex')})
            # row = self._cursor.fetchone()
            # value = str(row[0])
        # except TypeError:
            # raise KeyError, key
        # else:
            # if unpickle:
                # return pickle.loads(value)
            # else:
                # return value

    def __getitem__(self, key):
        try:
            return db.session.query(DhtData).filter_by(key=key).first().value
        except:
            raise KeyError, key

    def __delitem__(self, key):
        db.session.query(DhtData).filter_by(key=key).delete()
        db.session.commit()
