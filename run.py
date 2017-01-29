#!/usr/bin/env python
from pears import app, db
from pears import node
from twisted.internet import reactor, defer
from dht import dht
from pears.models import Profile
import numpy as np
import sys, os
import urllib
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource


def create_profile():
    db.create_all()

def parse_args(args):
    arg = dht.parse_arguments(args)
    port = arg.udp_port
    if arg.known_ip and arg.known_port:
        known_nodes = [(arg.known_ip, int(arg.known_port))]
    elif arg.config_file:
        known_nodes = []
        f = open(arg.config_file, 'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            ip_address, udp_port = line.split()
            known_nodes.append((ip_address, int(udp_port)))
    else:
        known_nodes = None
    return port, known_nodes

def get_dht_value():
    vector = (Profile.query.all()[0]).vector
    peer_profile = np.array(filter(None, [float(j) for j in
        vector.split(' ')]))
    KEY = dht.lsh(peer_profile)
    try:
        VALUE = urllib.urlopen('http://ip.42.pl/short').read().strip('\n')
    except:
        print "Unable to connect to the network. Setting up locally...\n"
        VALUE = "0.0.0.0"
    return KEY, VALUE

def main(args):
    port, known_nodes = parse_args(args)



    KEY, VALUE = get_dht_value()
    node.joinNetwork(known_nodes)
    reactor.callLater(0, dht.storeValue, KEY, VALUE, node)
    reactor.addSystemEventTrigger('before','shutdown', dht.cleanup, KEY,
            node)

    print "  * Starting the DHT in port {}".format(port)
    print "  * Running PeARS instance on http://0.0.0.0:5000/ (Press CTRL+C to quit)"

if __name__ == "__main__":
    create_profile()
    main(sys.argv)
    flask_app = WSGIResource(reactor, reactor.getThreadPool(),
            app)
    flask_site = Site(flask_app)
    reactor.listenTCP(5000, flask_site)
    reactor.run()



