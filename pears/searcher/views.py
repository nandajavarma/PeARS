#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from flask import render_template, request, Blueprint
import requests, json, urllib2, urllib
from ast import literal_eval
from dht import dht
import ConfigParser

from . import searcher

from pears.utils import read_pears, query_distribution, load_entropies, print_timing
from pears import best_pears, scorePages, app, db
from pears.models import Profile
node = None
result_v = None
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
root_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))

def printresult(result):
    global result_v
    result_v = result

@print_timing
def get_result_from_dht(node, query_dist):
    global result_v
    query_key = dht.lsh(query_dist)
    deferred = dht.getValue(node, query_key)
    deferred.addCallback(printresult)
    if result_v:
        return result_v
    else:
        try:
            my_ip = [urllib.urlopen('http://ip.42.pl/short').read().strip('\n')]
        except:
            my_ip = ["0.0.0.0"]
        return my_ip

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

@searcher.route('/')
@searcher.route('/index')
def index():
    global node, result_v
    results = []
    entropies_dict = load_entropies()
    query = request.args.get('q')
    if not node:
        node = create_dht_node()
    if not query:
        return render_template("index.html")
    else:
        #print "Making query distribution..."
        query_dist = query_distribution(query, entropies_dict)
        pear_details = []
        results = []
        if query_dist.size:
            get_result_from_dht(node, query_dist)
            pear_profiles = read_pears(result_v)
            pear_details = best_pears.find_best_pears(query_dist, pear_profiles)
            pear_ips = pear_details.keys()
            results = scorePages.runScript(query, query_dist, pear_ips)
        if not pear_details or not results:
          pears = ['no pear found :(']
          scorePages.ddg_redirect(query)
        elif not result_v:
            try:
              result_v = [urllib.urlopen('http://ip.42.pl/short').read().strip('\n')]
            except:
              result_v = ['0.0.0.0']

        results = get_cached_urls(results)
        return render_template('results.html', pears=result_v,
                               query=query, results=results)

