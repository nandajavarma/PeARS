import math
import os
import re
import sys

import numpy as np
from pears.overlap_calculation import generic_overlap
from pears.models import Urls, OpenVectors
from pears import app, db

def select_url(url1,url2):
  """For a pair of urls, choose the https if identical, shortest otherwise"""
  remove = ""
  u1 = url1.url
  u2 = url2.url
  if re.sub("https:","",u1) == re.sub("http:","",u2):
    remove = url2
  if re.sub("http:","",u1) == re.sub("https:","",u2):
    remove = url1
  if remove == "" and len(u1) < len(u2):
    remove = url2
  if remove == "" and len(u2) < len(u1):
    remove = url1
  if remove == "":
    remove = url1
  return remove


def list_duplicates(urls):
  duplicates = []
  for url1 in urls:
    u1 = url1.url
    for url2 in urls:
      if url2 != url1:
        u2 = url2.url
        if u1 != "" and u2 != "" and u1 != u2:
          if generic_overlap(u1,u2) > 0.9:
            print "Possible duplicates:",u1,u2
            to_remove = select_url(url1,url2)
            if to_remove not in duplicates:
              duplicates.append(to_remove)
    '''Checking there is still something left!'''
    if len(duplicates) == len(urls):
      del duplicates[-1]
  return duplicates

def remove_duplicates():
  all_duplicates = []
  urls = Urls.query.all()
  for u in urls:
    v = u.dists
    matches = db.session.query(Urls).filter_by(dists=v).all()
    if len(matches) > 1 :
      all_duplicates.extend(list_duplicates(matches))
      all_duplicates = list(set(all_duplicates))
  for u in all_duplicates:
    print "Deleting",u.url,"..."
    Urls.query.filter_by(url=u.url).delete()
    db.session.commit()


def clean_cache():
  cached_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk("./html_cache/") for f in filenames]
  for r in cached_files:
    url1=r.replace("./html_cache","http:/")
    url2=r.replace("./html_cache","https:/")
    if not db.session.query(Urls).filter_by(url=url1).all() and not db.session.query(Urls).filter_by(url=url2).all():
      print r,"is not in database! Deleting cached file..."
      os.remove(r)
    dir = re.sub("[^\/]*$","",r)
    if not os.listdir(dir):
      print dir,"is empty: removing directory..."
      os.rmdir(dir)

def runScript():
  print "Now cleaning up... removing duplicates..."
  remove_duplicates()



# when executing as script
if __name__ == '__main__':
    runScript() 
