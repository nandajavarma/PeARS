from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdocument import PDFDocument
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from cStringIO import StringIO
from StringIO import StringIO
import urllib2
from urllib2 import Request
import caching
import sys

#Thanks to https://quantcorner.wordpress.com/2014/03/16/parsing-pdf-files-with-python-and-pdfminer/

def convert_pdf_to_txt(url):
  try:
    open = urllib2.urlopen(Request(url)).read()

    memory_file = StringIO(open)
    parser = PDFParser(memory_file)
    document = PDFDocument(parser)

    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()

    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

    interpreter = PDFPageInterpreter(rsrcmgr, device)

    for page in PDFPage.create_pages(document):
      interpreter.process_page(page)

    text = retstr.getvalue()

    device.close()
    retstr.close()
  except:
    print "Error accessing/parsing the PDF file"
    return ""
  return text

def extract_from_url(url, cache):
  drows = []
  body = convert_pdf_to_txt(url)
  if body != "":
    lines = body.split('\n')
    body_str = ""
    c = 0
    title = ""
    for l in lines:
      '''Don't consider more than 200 lines (for long pdfs!)'''
      if c < 200:
        if title == "":
          title = l
        if l != "":
          body_str+=l+" "
      c+=1

    title = unicode(title, "utf-8")
    body_str = unicode(body_str, "utf-8")
    drows = [title, url, body_str, ""]
    if cache:
      caching.cache_pdf(url)

  return drows

