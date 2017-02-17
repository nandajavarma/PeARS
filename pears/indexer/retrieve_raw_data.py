import os
import re
import sys
import csv
import sqlite3
import numpy as np
import htmlparser, pdfparser, xowa, runDistSemWeighted
from pears.models import Urls,OpenVectors
from pears import db

drows = []
home_directory = os.path.expanduser('~')


def mk_ignore():
    #A small ignore list for sites that don't need indexing.
    ignore=["twitter", "google", "duckduckgo", "bing", "yahoo", "facebook",
            "mail.google.com", "whatsapp", "telegram"]
    '''Make ignore list'''
    s = []
    for i in ignore:
        s.append("www."+i)
        s.append("://"+i)
    return s


def get_firefox_history_db(in_dir):
  """Given a home directory it will search it for the places.sqlite file
  in Mozilla Firefox and return the path. This should work on Windows/
  Linux"""
  print "Finding Firefox DB history..."
  firefox_directory = in_dir + "/.mozilla/firefox"
  for files in os.walk(firefox_directory):
    # Build the filename
    if re.search('places.sqlite', str(os.path.join(files))):
      history_db = str(os.path.realpath(files[0]) + '/places.sqlite')
      # print history_db
      return history_db
  return None

def record_urls_to_process(db_urls, num_pages):
    '''Select and write urls that will be clustered.'''
    print "Now writing the",num_pages,"pages to process..."
    ignore_list = mk_ignore()
    urls_to_process = []
    i = 0
    for url_str in db_urls:

        url = unicode(url_str[1])
        if i < num_pages:
            if not any( i in url for i in ignore_list):
                if not url.startswith('http'):
                    continue
                url = url.replace('http://', 'https://').rstrip('/')
                if url not in urls_to_process:
                    if "www" not in url:
                        url_with_www = url.replace("https://", "https://www.")
                        if url_with_www in urls_to_process:
                            continue
                    else:
                        url_with_www = url
                    if not db.session.query(Urls).filter_by(url=url).all():
                      urls_to_process.append(url)
                      print "...writing",url,"..."
                      i+=1
                    else:
                      print url,"is already known..."
        else:
          print "Recorded",len(urls_to_process),"urls..."
          break

    return urls_to_process




def index_history(num_pages):
  # [TODO] Set the firefox path here via config file
  HISTORY_DB = get_firefox_history_db(home_directory)
  if HISTORY_DB is None:
    print 'Error - Cannot find the Firefox history database.\n\nExiting...'
    sys.exit(1)

  # connect to the sqlite history database
  firefox_db = sqlite3.connect(HISTORY_DB)
  cursor = firefox_db.cursor()

  # get the list of all visited places via firefox browser
  cursor.execute("SELECT * FROM 'moz_places' ORDER BY last_visit_date DESC")
  rows = cursor.fetchall()

  urls_to_process = record_urls_to_process(rows, int(num_pages))
  firefox_db.close()
  return urls_to_process


def index_from_file(filename):
  f = open(filename,'r')
  urls_to_process = []
  for url in f:
    url = url.rstrip('\n')
    www_url = xowa.local_to_www(url)
    if not db.session.query(Urls).filter_by(url=www_url).all():
      urls_to_process.append(url)
      print "...to process:",url,"..."
    else:
      print url,"is already known..."
  return urls_to_process

def index_url(urls_to_process, cache):
    for url in urls_to_process:
        print "Indexing '{}'\n".format(url)
        if ".pdf" in url:
          drows = pdfparser.extract_from_url(url,cache)
        else:
          drows = htmlparser.extract_from_url(url, cache)
        if drows:
            u = Urls(url=unicode(url))
            u.title = unicode(drows[0])
            u.url = unicode(drows[1])
            u.body = unicode(drows[2])
            u.wordclouds = unicode(drows[3])
            u.private = False
            db.session.add(u)
            db.session.commit()
    runDistSemWeighted.runScript()

def runScript(*args):
  '''Run script, either by indexing part of history or by indexing the urls
  provided by the user'''

  urls_to_process = []
  switch = args[0]
  arg = args[1]
  cache = False
  if len(args) == 3 and args[2] == "cache":
    cache = True

  if switch == "history":
    urls_to_process = index_history(arg)
  if switch == "file":
    urls_to_process = index_from_file(arg)

  index_url(urls_to_process, cache)

if __name__ == '__main__':
  runScript(sys.argv)
