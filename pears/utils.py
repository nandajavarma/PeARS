import os, cStringIO
import time, requests, urllib2, numpy
from sqlalchemy.types import PickleType
from dht.entangled.kademlia.contact import Contact
import getpass
import socket

from numpy import linalg, array, dot, sqrt, math

from .models import OpenVectors, Profile
from pears import db

stopwords = ["", "(", ")", "a", "about", "an", "and", "are", "around", "as", "at", "away", "be", "become", "became",
             "been", "being", "by", "did", "do", "does", "during", "each", "for", "from", "get", "have", "has", "had",
             "her", "his", "how", "i", "if", "in", "is", "it", "its", "made", "make", "many", "most", "of", "on", "or",
             "s", "some", "that", "the", "their", "there", "this", "these", "those", "to", "under", "was", "were",
             "what", "when", "where", "who", "will", "with", "you", "your"]

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
pears_dict = {}

# For debug purposes.
def tracefunc(frame, event, arg, indent=[0]):
      if event == "call":
          indent[0] += 2
          print "-" * indent[0] + "> call function", frame.f_code.co_name
      elif event == "return":
          print "<" + "-" * indent[0], "exit function", frame.f_code.co_name
          indent[0] -= 2
      return tracefunc


def print_timing(func):
    """ Timing function, just to know how long things take """
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s in scorePages took %0.3f ms' % (func.func_name, (t2 - t1) * 1000.0)
        return res

    return wrapper

def convert_to_array(vector):
  return array([float(i) for i in vector.split(',')])

def sim_to_matrix(vec, n):
    """ Compute similarities and return top n """
    cosines = {}
    c = 0
    for entry in OpenVectors.query.all():
      cos = cosine_similarity(numpy.array(vec), convert_to_array(entry.vector))
      cosines[entry.word] = cos

    topics = []
    topics_s = ""
    c = 0
    for t in sorted(cosines, key=cosines.get, reverse=True):
        if c < n:
            if t.isalpha() and t not in stopwords:
                topics.append(t)
                topics_s += t + " "
                c += 1
        else:
            break
    print "Nearest neighbours for profile:",topics_s
    return topics, topics_s[:-1]

def normalise(v):
    norm = linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def cosine_similarity(peer_v, query_v):
    if len(peer_v) != len(query_v):
        raise ValueError("Peer vector and query vector must be "
                         " of same length")
    num = dot(peer_v, query_v)
    den_a = dot(peer_v, peer_v)
    den_b = dot(query_v, query_v)
    return num / (sqrt(den_a) * sqrt(den_b))

@print_timing
def load_entropies(entropies_file=os.path.join(root_dir, 'demo/ukwac.entropy.txt')):
    entropies_dict = {}
    with open(entropies_file, "r") as entropies:
        for line in entropies:
            word, score = line.split('\t')
            word = word.lower()
            # Must have this cos lower() can match two instances of the same word in the list
            if word.isalpha() and word not in entropies_dict:
                entropies_dict[word] = float(score)

    return entropies_dict

@print_timing
def query_distribution(query, entropies):
    """ Make distribution for query """
    words = query.rstrip('\n').split()
    # Only retain arguments which are in the distributional semantic space
    vecs_to_add = []
    for word in words:
        word_db = OpenVectors.query.filter(OpenVectors.word == word).first()
        if word_db:
          vecs_to_add.append(word_db)
        else:
          unknown = get_unknown_word(word)
          if unknown:
            vecs_to_add.append(unknown)

    vbase = array([])
    # Add vectors together
    if vecs_to_add:
        # Take first word in vecs_to_add to start addition
        vbase = array([float(i) for i in vecs_to_add[0].vector.split(',')])
        for vec in vecs_to_add[1:]:
            if vec.word in entropies and math.log(entropies[vec.word] + 1) > 0:
                weight = float(1) / float(math.log(entropies[vec.word] + 1))
                vbase = vbase + weight * array([float(i) for i in vec.vector.split(',')])
            else:
                vbase = vbase + array([float(i) for i in vec.vector.split(',')])

    vbase = normalise(vbase)
    return vbase

def printresult(result, ip):
    global pears_dict
    vector = result[0].response[0]
    val = cStringIO.StringIO(str(vector))
    pears_dict[ip] = numpy.loadtxt(val)

def errorprint(result, ip):
    global pears_dict
    vector = (Profile.query.all()[0]).vector
    val = cStringIO.StringIO(str(vector))
    pears_dict[ip] = numpy.loadtxt(val)


@print_timing
def read_pears(pears):
    global pears_dict
    profile = Profile.query.first()
    try:
        my_ip = urllib.urlopen('http://ip.42.pl/short').read().strip('\n')
    except:
        my_ip = "0.0.0.0"
    if not pears:
        p = profile.vector
        val = cStringIO.StringIO(str(p))
        pears_dict[my_ip] = numpy.loadtxt(val)
    else:
        for cont in pears:
            if not type(cont) == Contact:
                if cont == my_ip:
                    p = profile.vector
                    val = cStringIO.StringIO(str(p))
                    pears_dict[my_ip] = numpy.loadtxt(val)
                else:
                    pass
            else:
                ret = getattr(cont, 'getProfile')
                df = ret(rawResponse=True)
                df.addCallback(printresult, cont.address)
                df.addErrback(errorprint, my_ip)

                time.sleep(1)

    return pears_dict


def get_unknown_word(word):
  print "Fetching",word
  try:
    r = requests.get("http://api.openmeaning.org/vectors/"+word+"/")
    print r.status_code
    if r.status_code == 200:
      openvectors = OpenVectors()
      openvectors.word = unicode(word)
      openvectors.vector = r.json()['vector']
      db.session.add(openvectors)
      db.session.commit()
      return openvectors
    return False
  except:
    print "Problem fetching word..."
    return
