""" Compares the query to each document
Called by ./mkQueryPage.py
"""

import os, requests, urllib
import re
import sys
import urllib
import webbrowser
from operator import itemgetter
from pears import db
import socket
import math
import numpy
from ast import literal_eval
import time


from overlap_calculation import score_url_overlap, generic_overlap
from .utils import query_distribution, cosine_similarity, print_timing
from .models import Urls
import cStringIO

urls = None

@print_timing
def scoreDS(query_dist, pear_urls):
    """ Get distributional score """
    DS_scores = {}
    wordclouds = {}
    titles = {}
    for val in pear_urls:
        url = val['url']
        doc_dist = val['dists']
        d = cStringIO.StringIO(str(doc_dist))
        vector = numpy.loadtxt(d)
        wordclouds[url] = val['wordclouds']
        titles[url] = val['title']
        if vector.all():
            score = cosine_similarity(vector, query_dist)
            if score > 0.4:  # Doc must be good enough
                DS_scores[url] = score
        else:
            Urls.query.filter_by(url=url).delete()
            db.session.commit()
    return DS_scores, wordclouds, titles


def scoreURL(query, pear_urls):
    """ Get url overlap score """
    URL_scores = {}
    for val in pear_urls:
      url = val['url']
      URL_scores[url] = score_url_overlap(query, url)
    return URL_scores

def scoreTitles(query, pear_urls):
  """Get overlap score between title and query"""
  title_scores = {}
  for val in pear_urls:
    url = val['url']
    title = val['title']
    title_scores[url] = generic_overlap(query, title)
  return title_scores

@print_timing
def scoreDocs(query, query_dist, pear_urls):
    """ Score documents for a pear """
    document_scores = {}  # Document scores
    DS_scores, wordclouds, titles = scoreDS(query_dist, pear_urls)
    URL_scores = scoreURL(query, pear_urls)
    title_scores = scoreTitles(query, pear_urls)
    for val in pear_urls:
        v = val['url']
        if v in DS_scores and v in URL_scores:
            url_bonus = 0
            title_bonus = 0
            if URL_scores[v] > 0.7:
                url_bonus = URL_scores[v] * 0.2
            if title_scores[v] > 0.7:
                title_bonus = title_scores[v] * 0.2
            if DS_scores[v] > 0.2:
                document_scores[v] = DS_scores[v] + url_bonus + title_bonus  # Boost DS score by a maximum of 0.2
            else:
                document_scores[v] = DS_scores[v]
            if math.isnan(document_scores[v]):  # Check for potential NaN -- messes up with sorting in bestURLs.
                document_scores[v] = 0
    return document_scores, wordclouds, titles


def bestURLs(doc_scores):
    best_urls = []
    c = 0
    for w in sorted(doc_scores, key=doc_scores.get, reverse=True):
        if c < 50:
          best_urls.append(w)
          c += 1
        else:
            break
    return best_urls


def ddg_redirect(query):
    print "No suitable pages found."
    duckquery = ""
    for w in query.rstrip('\n').split():
        duckquery = duckquery + w + "+"
    webbrowser.open_new_tab(
            "https://duckduckgo.com/?q=" +
            duckquery.rstrip('+'))
    return

def output(best_urls, url_titles, url_wordclouds):
    results = []
    # If documents matching the query were found on the pear network...
    if len(best_urls) > 0:
        for u in best_urls:
            results.append([u, url_titles[u], url_wordclouds[u]])

    # Otherwise, open duckduckgo and send the query there
    else:
        results = []
    return results

def printres(result):
    print result
    global urls
    urls =  result

def noconnection(result):
    print "nothing"

@print_timing
def get_pear_urls(contact):
    global urls
    try:
        my_ip = urllib.urlopen('http://ip.42.pl/short').read().strip('\n')
    except:
        my_ip = "0.0.0.0"
    if not hasattr(contact, 'address') or contact.address == my_ip:
        urls = Urls.query.all()
        return [u.__dict__ for u in urls]
    else:
        ret = getattr(contact, 'getUrls')
        df = ret(rawResponse=True)
        df.addCallback(printres)
        df.addErrback(noconnection)
    time.wait(1)
    return urls

def runScript(query, query_dist, pears):
    url_wordclouds = {}
    url_titles = {}
    best_urls = []
    for pear in pears:
        pear_urls = get_pear_urls(pear)
        document_scores, wordclouds, titles = scoreDocs(query, query_dist, pear_urls)	#with URL overlap
        #document_scores, wordclouds = scoreDS(query_dist, pear_urls)  # without URL overlap
        url_wordclouds.update(wordclouds)
        url_titles.update(titles)
        best_urls = bestURLs(document_scores)
    return output(best_urls, url_titles, url_wordclouds)


if __name__ == '__main__':
    runScript(sys.argv[1], sys.argv[2], sys.argv[3])
