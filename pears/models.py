from pears import db


class OpenVectors(db.Model):
    __bind_key__ = 'openvectors'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.UnicodeText(64))
    vector = db.Column(db.Text)

class DhtData(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    key = db.Column(db.UnicodeText())
    lastPublished= db.Column(db.UnicodeText())
    originallyPublished= db.Column(db.UnicodeText())
    originalPublisherID= db.Column(db.UnicodeText())


class Urls(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    url = db.Column(db.UnicodeText())
    body = db.Column(db.UnicodeText())
    title = db.Column(db.UnicodeText())
    dists = db.Column(db.String(7000))
    wordclouds = db.Column(db.String(1000))
    private = db.Column(db.Boolean, default = False)


    def __init__(self, url=None, dists=None, wordclouds=None,
            title=None, body=None, private=None):
        self.url = url
        self.dists = dists
        self.wordclouds = wordclouds
        self.body = body
        self.title = title
        self.private = private

    def __repr__(self):
        return self.url

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64))
    vector = db.Column(db.Text)
    coherence = db.Column(db.Float)
    topics = db.Column(db.UnicodeText)

    def __init__(self, name=None, vector=None, coherence=None,
            topics=None):
        self.name = name
        self.vector = vector
        self.coherence = coherence
        self.topics = topics

    def __repr__(self):
        return self.name

