#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, re
import requests
from io import StringIO
import cStringIO
import argparse, socket, urllib
import numpy, math
from twisted.internet import reactor
from common_vars import alpha, beta, W
from entangled.node import EntangledNode
from entangled.kademlia.datastore import SQLiteDataStore
from twisted.internet.protocol import Factory, Protocol
import  subprocess
from pears.models import Profile

def storeValue(key, value, node):
    """ Stores the specified value in the DHT using the specified key """
    print '\nStoring value; Key: %s, Value: %s' % (key, value)
    # Store the value in the DHT. This method returns a Twisted Deferred result, which we then add callbacks to
    deferredResult = node.iterativeStore(key, value)
    return deferredResult

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
    deferredResult.addCallback(getValueCallback, node=node, key=key)
    # As before, add the generic error callback
    deferredResult.addErrback(genericErrorCallback)
    return deferredResult


def getValueCallback(result, node, key):
    """ Callback function that is invoked when the getValue() operation succeeds """
    if type(result) == dict:
        IPs = result.values()
    else:
        IPs = "0.0.0.0"

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
