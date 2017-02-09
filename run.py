#!/usr/bin/env python
from pears import app, db
from twisted.internet import reactor
from dht import dht
import sys, os
import urllib
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
import ConfigParser


def create_profile():
    db.create_all()

def parse_args(args):
    arg = dht.parse_arguments(args)
    port = arg.udp_port
    if arg.known_ip and arg.known_port:
        known_nodes = [(arg.known_ip, arg.known_port)]
    elif arg.config_file:
        known_nodes = []
        f = open(arg.config_file, 'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            ip_address, udp_port = line.split()
            known_nodes.append((ip_address, udp_port))
    else:
        known_nodes = []
    return port, known_nodes


def main(args, tcp_port):
    port, known_nodes = parse_args(args)
    known_nodes = filter(None, known_nodes)
    config = ConfigParser.ConfigParser(allow_no_value=True)
    nodefile =  os.path.join(os.getcwd(), 'dht.nodes')
    with open(nodefile, 'w') as f:
        config.add_section('port')
        config.set('port', str(port))
        if known_nodes:
            config.add_section('known_nodes')
            for (k,v) in known_nodes:
                config.set('known_nodes', str(k), str(v))
        config.write(f)


    print "  * Running PeARS instance on http://0.0.0.0:{}/ (Press " \
                                        "CTRL+C to quit)".format(tcp_port)

if __name__ == "__main__":
    tcp_port = 5000
    create_profile()
    flask_app = WSGIResource(reactor, reactor.getThreadPool(), app)
    flask_site = Site(flask_app)
    reactor.listenTCP(tcp_port, flask_site)
    client = app.test_client()
    reactor.callLater(0, client.get, '/index')
    main(sys.argv, tcp_port)
    reactor.run()



