#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse, urllib
import numpy
from twisted.internet import reactor, defer
from common_vars import alpha, beta, W
from entangled.node import EntangledNode
from entangled.kademlia.datastore import DictDataStore
from entangled.kademlia.contact import Contact
from pears.models import Profile
import numpy as np
from ast import literal_eval


def genericErrorCallback(failure):
    """ Callback function that is invoked if an error occurs during any of the DHT operations """
    print 'An error has occurred:', failure.getErrorMessage()
    reactor.callLater(0, stop)

def stop():
    """ Stops the Twisted reactor, and thus the script """
    print '\nStopping Kademlia node and terminating script...'
    reactor.stop()

def getValue(node, key):
    """ Retrieves the value of the specified key (KEY) from the DHT """
    # Get the value for the specified key (immediately returns a Twisted deferred result)
    print '\nRetrieving value from DHT for key "%s"...' % key
    deferredResult = node.iterativeFindValue(key)
    # Add a callback to this result; this will be called as soon as the operation has completed
    deferredResult.addCallback(getValueCallback, key=key)
    # As before, add the generic error callback
    deferredResult.addErrback(genericErrorCallback)
    return deferredResult


def getValueCallback(result, key):
    """ Callback function that is invoked when the getValue() operation succeeds """
    IPs = []
    callback_refs = []
    if type(result) == dict:
        IPs = [literal_eval(val) for val in result.values()]
        IPs = [ip for ip, port in IPs]
    elif type(result) == list:
        for cont in result:
            if type(cont) == Contact:
                IPs.append(cont)
    IPs = ["0.0.0.0"] if not IPs else IPs
    # print 'Value successfully retrieved: %s' % IPs
    return IPs

def lsh(vector):
    alpha.seek(0)
    alpha_array = numpy.loadtxt(alpha)
    lsh_hash = (numpy.dot(alpha_array, vector) + beta)%W
    return str(lsh_hash)

def cleanup(KEY, node):
    """ Removes the the specified key (KEY) its associated value from the DHT """
    print '\nDeleting key/value from DHT...'
    deferredResult = node.iterativeDelete(KEY)
    # Add our callback
    deferredResult.addCallback(deleteValueCallback)
    # As before, add the generic error callback
    deferredResult.addErrback(genericErrorCallback)


def deleteValueCallback(result):
    """ Callback function that is invoked when the deleteValue() operation succeeds """
    print 'Key/value pair deleted'
    # Stop the script after 1 second
    reactor.callLater(1.0, stop)


def stop():
    """ Stops the Twisted reactor, and thus the script """
    print '\nStopping Kademlia node and terminating script...'
    reactor.stop()

def parse_arguments(args=None):
    usage = "create_network [UDP_PORT] [KNOWN_NODE_IP  KNOWN_NODE_PORT] "\
    "[-f FILE_WITH_KNOWN_NODES]"
    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('udp_port', type=int, default=4000,
            help="The UDP port that is to be used", nargs='?')
    parser.add_argument('-f', dest='config_file', help="File with known "\
            "nodesit should containg one IP address and UDP port\n"\
            "per line, seperated by a space.", type=argparse.FileType('rt'))
    parser.add_argument('known_ip', help="IP address of the known node"\
                "in the DHT", nargs='?')
    parser.add_argument('known_port', help="Port number of the known node"\
                "in the DHT", type=int, nargs='?')
    args = parser.parse_args()
    if args.known_ip or args.known_port:
        required_together = ('known_port','known_ip')
        if not all([getattr(args,x) for x in required_together]):
            raise RuntimeError("Cannot supply Known Node IP without"\
                " Known IP port")
    else:
        print "\nNOTE: You have not specified any remote DHT node(s) to connect to."
        print "It will thus not be aware of any existing DHT, but will still "\
                "function as a self-contained DHT (until another node "\
                "contacts it).\n"
    return args

def get_dht_value(port):
    vector = (Profile.query.all()[0]).vector
    vector = vector.strip('[]\n\t\r')
    peer_profile = np.array([np.float64(j) for j in vector.split(' ')])
    KEY = lsh(peer_profile)
    try:
        VALUE = str((urllib.urlopen('http://ip.42.pl/short').read().strip('\n'),
                port))
    except:
        print "Unable to connect to the network. Setting up locally...\n"
        VALUE = str(("0.0.0.0", port))
    return KEY, VALUE

def bootstrap_dht(port, known_nodes):
    if os.path.isfile('/tmp/dbFile%s.db' % port):
        os.remove('/tmp/dbFile%s.db' % port)
    data_store = DictDataStore()
    node = EntangledNode(udpPort=int(port), dataStore=data_store)
    KEY, VALUE = get_dht_value(port)
    node.joinNetwork(known_nodes)
    node.iterativeStore(KEY, VALUE)
    reactor.addSystemEventTrigger('before','shutdown', cleanup, KEY, node)
    return node
