#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, time
import re
from flask import render_template, request, Blueprint
from dht.entangled.kademlia.contact import Contact
import requests, json, urllib2, urllib
from ast import literal_eval
from dht import dht
import ConfigParser

from . import searcher

from pears.utils import read_pears, query_distribution, load_entropies, print_timing
from pears import best_pears, scorePages, app, db
from pears.models import Profile
node = None
result_v = []
port = None
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
root_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))

@print_timing
def get_result_from_dht(node, query_dist):
    global port, result_v
    query_key = dht.lsh(query_dist)
    deferred = dht.getValue(node, query_key)
    return deferred

def get_cached_urls(urls):
  urls_with_cache = urls
  for u in urls_with_cache:
      cache = re.sub(r"http\:\/\/|https\:\/\/", root_dir+"/html_cache/", u[0])
      if os.path.exists(cache):
        u.append("file://"+cache)
      else:
        u.append(u[0])
  return urls_with_cache

def create_dht_node():
    global port
    nodefile =  os.path.join(os.getcwd(), 'dht.nodes')
    with open(nodefile) as fp:
        config = ConfigParser.ConfigParser(allow_no_value=True)
        config.readfp(fp)
        try:
            port = int(config.items('port')[0][0])
        except:
            print "Error: Port information missing"
            sys.exit()
        try:
            known_nodes = config.items('known_nodes')
            known_nodes = [(k, int(v)) for (k, v) in known_nodes]
        except:
            known_nodes = []

    print "  * Starting the DHT in port {}".format(port)
    ret = dht.bootstrap_dht(port, known_nodes)
    return ret

def get_my_ip():
    try:
        return urllib.urlopen('http://ip.42.pl/short').read().strip('\n')
    except:
        return "0.0.0.0"

def format_output(results):
    pears = []
    urls = []
    if not results:
        pears = ['no pear found :(']
        scorePages.ddg_redirect(query)
        return pears, urls
    for each in results:
        pears.extend(each[-1].keys())
        urls.extend(each[-1].values())

    if not pears or not urls:
        return pears, urls
    results = get_cached_urls(urls[0])
    ips = []
    for ret in pears:
        if type(ret) == Contact:
            ips.append(ret.address)
        else:
            ips.append(ret[0])
    return ips, results


@searcher.route('/')
@searcher.route('/index')
def index():
    global node
    results = []
    pears = []
    entropies_dict = load_entropies()
    query = request.args.get('q')
    if not node:
        node = create_dht_node()
    if not query:
        return render_template("index.html")
    else:
        my_ip = get_my_ip()
        query_dist = query_distribution(query, entropies_dict)
        pear_details = []
        if query_dist.size:
            deferred = get_result_from_dht(node, query_dist)
            deferred.addCallback(read_pears, node, my_ip)
            deferred.addCallback(best_pears.find_best_pears, query_dist)

            deferred.addCallback(scorePages.runScript, query,
                    query_dist, my_ip)
            deferred.addCallback(format_output)
            if deferred.result:
                pears = deferred.result[0]
                results = deferred.result[-1]
            return render_template('results.html', pears=pears,
                                   query=query, results=results)
