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
  #print "Length of urls:",len(urls)
  duplicates = []
  i=0
  for i in range(len(urls)-1):
    u1 = urls[i].url
    j=0
    for j in range(i+1,len(urls)):
      u2 = urls[j].url
      #print i,u1,j,u2
      if u1 != "" and u2 != "" and u1 != u2:
        if generic_overlap(u1,u2) > 0.9:
          #print "Possible duplicates:",u1,u2
          to_remove = select_url(urls[i],urls[j])
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
      new_duplicates = list_duplicates(matches)
      for n in new_duplicates:
        if n not in all_duplicates:
          all_duplicates.append(n)
  for u in all_duplicates:
    print "Deleting",u.url,"..."
    Urls.query.filter_by(url=u.url).delete()
    db.session.commit()


def clean_cache():
  cached_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk("./html_cache/") for f in filenames]
  for r in cached_files:
    '''Special case: url is dir and cached file is index.html'''
    if "index.html" in r:
      r=r.replace("index.html","")
    url1=unicode(r.replace("./html_cache","http:/"))
    url2=unicode(r.replace("./html_cache","https:/"))
    if not db.session.query(Urls).filter_by(url=url1).all() and not db.session.query(Urls).filter_by(url=url2).all():
      print r,"is not in database! Deleting cached file..."
      try:
        os.remove(r)
      except:
        print "Problem deleting..."
    dir = re.sub("[^\/]*$","",r)
    if not os.listdir(dir):
      print dir,"is empty: removing directory..."
      os.rmdir(dir)

def runScript():
  print "\nNow cleaning up... removing duplicates..."
  remove_duplicates()
  print "\nCleaning cache..."
  clean_cache()


# when executing as script
if __name__ == '__main__':
    runScript()
