import re
import sys
import caching
import requests
import detect_open, xowa
from urllib2 import HTTPError
from bs4 import BeautifulSoup
from langdetect import detect


def extract_from_url(url, cache):
  '''From history info, extract url, title and body of page,
  cleaned with BeautifulSoup'''
  drows = []
  try:
    try:
      req = requests.get(unicode(url), allow_redirects=True, timeout=20)
    except (requests.exceptions.SSLError or requests.exceptions.Timeout) as e:
      #print "\nCaught the exception: {0}. Trying with http...\n".format(str(e))
      url = unicode(url.replace("https", "http"))
      req = requests.get(url, allow_redirects=True)
    except requests.exceptions.RequestException as e:
      #print "Ignoring {0} because of error {1}\n".format(url, str(e))
      print "Ignoring {0} because of error...\n".format(url)
      return
    except requests.exceptions.HTTPError as err:
      #print str(err)
      return
    req.encoding = 'utf-8'
    if req.status_code is not 200:
      print "Warning: "  + str(req.url) + ' has a status code of: ' \
        + str(req.status_code) + ' omitted from database.\n'
    bs_obj = BeautifulSoup(unicode(req.text),"lxml")
    if hasattr(bs_obj.title, 'string') & (req.status_code == requests.codes.ok):
      try:
        title = xowa.xowa_to_www_title(unicode(bs_obj.title.string))
        if url.startswith('http'):
          if title is None:
            title = u'Untitled'
          checks = ['script', 'style', 'meta', '<!--']
          for chk in bs_obj.find_all(checks):
            chk.extract()
          body = unicode(bs_obj.get_text())
          pattern = re.compile('(^[\s]+)|([\s]+$)', re.MULTILINE)
          body_str=re.sub(pattern," ",body)
          if detect(body_str) != "en":
            print "Ignoring",url,"because language is not supported."
            return
          www_url = xowa.local_to_www(url)
          wordcloud = detect_open.try_snippet(url,bs_obj)
          drows = [title, www_url, body_str, wordcloud]
        if title is None:
          title = u'Untitled'
      except HTTPError as error:
        title = u'Untitled'
      except None:
        title = u'Untitled'
        #print "Processed",url,"..."
    if cache:
      caching.runScript(url,unicode(req.text))
    return drows
    # can't connect to the host
  except:
    error = sys.exc_info()[0]
    #print "Error - %s" % error

