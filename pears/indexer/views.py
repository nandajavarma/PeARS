from . import indexer

@indexer.route('/indexer')
def hello():
    return "Hello!"
