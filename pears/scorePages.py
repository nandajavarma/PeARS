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
from twisted.internet import defer


from overlap_calculation import score_url_overlap, generic_overlap
from .utils import query_distribution, cosine_similarity, print_timing
from .models import Urls
import cStringIO

urls = None
results = []


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
            try:
                results.append([u, url_titles[u], url_wordclouds[u]])
            except:
                results.append([u, '', ''])

    # Otherwise, open duckduckgo and send the query there
    else:
        results = []
    return results


def local_url_search(query, query_dist):
    urls = Urls.query.all()
    pear_urls = [u.__dict__ for u in urls]
    document_scores, wordclouds, titles = scoreDocs(query, query_dist, pear_urls)	#with URL overlap
    best_urls = bestURLs(document_scores)
    return output(best_urls, titles, wordclouds)

def printresult(result, cont):
    return { cont: literal_eval(result[0].response)}

def errorfunc(failure):
    """ Callback function that is invoked if an error occurs during any of the DHT operations """
    print 'An error has occurred:', failure.getErrorMessage()
    reactor.callLater(0, stop)

def return_updated_data():
    global results
    return results

def runScript(result, query, query_dist, my_ip):
    pears = result.keys()
    _dlist = []
    for pear in pears:
        if not hasattr(pear, 'address') or pear.address in [my_ip, "0.0.0.0"]:
            df = defer.Deferred()
            output = local_url_search(query, query_dist)
            df.callback({pear: output})
        else:
            func = getattr(pear, 'getUrls')
            df = func(str(query), str(query_dist), rawResponse=True)
            df.addCallback(printresult, pear)
            df.addErrback(errorfunc)
        _dlist.append(df)
    return defer.DeferredList(_dlist)


if __name__ == '__main__':
    runScript(sys.argv[1], sys.argv[2], sys.argv[3])
