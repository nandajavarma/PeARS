""" Compares the query to each document
Called by ./mkQueryPage.py
"""

import os
import re
import sys
import urllib
import webbrowser
from operator import itemgetter

from numpy import *

import getUrlOverlap
from .utils import query_distribution, cosine_similarity, print_timing


def scoreDS(query_dist, url_dict):
    """ Get distributional score """
    DS_scores = {}
    for url, doc_dist in url_dict.items():
        score = cosine_similarity(doc_dist, query_dist)
        DS_scores[url] = score
    return DS_scores


def scoreURL(query, url_dict):
    """ Get url overlap score """
    URL_scores = {}
    for u in url_dict:
        URL_scores[u] = getUrlOverlap.runScript(query, u)
    return URL_scores


def getUrlDict(pear):
    """ Get URL-vector dict """
    url_dict = {}
    doc_dists = open(pear + "/urls.dists.txt")
    for l in doc_dists:
        l = l.rstrip('\n')
        fields = l.split()
        url = fields[0]
        doc_dist = [float(i) for i in fields[1:]]
        url_dict[url] = doc_dist
    doc_dists.close()
    return url_dict


def loadWordClouds(pear):
    """ Get word clouds for a pear """
    print "Loading word clouds..."
    url_wordclouds = {}
    word_clouds = open(pear + "/wordclouds.txt")
    for l in word_clouds:
        l = l.rstrip('\n')
        fields = l.split()
        url = fields[0]
        cloud = ""
        for f in fields[1:]:
            cloud += f + " "
        cloud = cloud[:-1]
        url_wordclouds[url] = cloud

    word_clouds.close()
    return url_wordclouds


def scoreDocs(query, query_dist, url_dict):
    """ Score documents for a pear """
    document_scores = {}  # Document scores
    DS_scores = scoreDS(query_dist, url_dict)
    URL_scores = scoreURL(query, url_dict)
    for v in url_dict:
        if v in DS_scores and v in URL_scores:
            # If URL overlap high (0.2 because of averag e length of
            # query=4 -- see getUrlOverlap --  and similarity okay
            if URL_scores[v] > 0.7 and DS_scores[v] > 0.2:
                document_scores[v] = DS_scores[v] + URL_scores[v] * 0.2  # Boost DS score by a maximum of 0.2
            else:
                document_scores[v] = DS_scores[v]
        if math.isnan(document_scores[v]):  # Check for potential NaN -- messes up with sorting in bestURLs.
            document_scores[v] = 0
    return document_scores


def bestURLs(doc_scores):
    best_urls = []
    c = 0
    for w in sorted(doc_scores, key=doc_scores.get, reverse=True):
        if c < 50:
            best_urls.append(w)
            print w, doc_scores[w]
            c += 1
        else:
            break
    return best_urls


def output(best_urls, query, url_wordclouds):
    results = []
    # If documents matching the query were found on the pear network...
    if len(best_urls) > 0:
        for u in best_urls:
            results.append([u, url_wordclouds[u]])

    # Otherwise, open duckduckgo and send the query there
    else:
        print "No suitable pages found."
        duckquery = ""
        for w in query.rstrip('\n').split():
            duckquery = duckquery + w + "+"
        webbrowser.open_new_tab(
                "https://duckduckgo.com/?q=" +
                duckquery.rstrip('+'))
        link_snippet_pair = [
            "###", "No suitable recommendation. You were redirected to duckduckgo."]
        results.append(link_snippet_pair)

    return results


def runScript(query, query_dist, pears):
    all_pears_doc_scores = {}  # Document scores
    all_url_wordclouds = {}
    for pear in pears:
        if pear.endswith('/'):
            pear = pear[:-1]
        wc = loadWordClouds(pear)
        for k, v in wc.items():
            all_url_wordclouds[k] = v
        url_dict = getUrlDict(pear)
        # document_scores=scoreDocs(query, query_dist, url_dict):	#with URL overlap
        document_scores = scoreDS(query_dist, url_dict)  # without URL overlap
        for k, v in document_scores.items():
            if v > 0.3:  # Doc must be good enough
                all_pears_doc_scores[k] = v
    best_urls = bestURLs(all_pears_doc_scores)
    return output(best_urls, query, all_url_wordclouds)


if __name__ == '__main__':
    runScript(sys.argv[1], sys.argv[2], sys.argv[3])
