import os
import time

from numpy import linalg, array, dot, sqrt, math

from .models import OpenVectors

stopwords = ["", "(", ")", "a", "about", "an", "and", "are", "around", "as", "at", "away", "be", "become", "became",
             "been", "being", "by", "did", "do", "does", "during", "each", "for", "from", "get", "have", "has", "had",
             "her", "his", "how", "i", "if", "in", "is", "it", "its", "made", "make", "many", "most", "of", "on", "or",
             "s", "some", "that", "the", "their", "there", "this", "these", "those", "to", "under", "was", "were",
             "what", "when", "where", "who", "will", "with", "you", "your"]

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


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


def load_entropies(entropies_file='demo/ukwac.entropy.txt'):
    entropies_dict = {}
    with open(entropies_file, "r") as entropies:
        for line in entropies:
            word, score = line.split('\t')
            word = word.lower()
            # Must have this cos lower() can match two instances of the same word in the list
            if word.isalpha() and word not in entropies_dict:
                entropies_dict[word] = float(score)

    return entropies_dict


def query_distribution(query, entropies):
    """ Make distribution for query """
    words = query.rstrip('\n').split()

    # Only retain arguments which are in the distributional semantic space
    vecs_to_add = []
    for word in words:
        word = OpenVectors.query.filter(OpenVectors.word == word).first()
        if word:
            vecs_to_add.append(word)
        else:
            word = word[0].upper() + word[1:]  # Did user carelessly forget to capitalise a proper noun?
            word = OpenVectors.query.filter(OpenVectors.word == word).first()
            if word:
                vecs_to_add.append(word)

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


def read_pears():
    shared_pears_ids = os.path.join(
            os.path.dirname(__file__),
            "shared_pears_ids.txt")

    pears_ids = {}
    with open(shared_pears_ids, 'r') as pears_file:
        for line in pears_file:
            items = line.split()
            pear_name = root_dir + "/" + items[0]
            pear_dist = [float(i) for i in items[1:]]
            pears_ids[pear_name] = pear_dist

    return pears_ids


def print_timing(func):
    """ Timing function, just to know how long things take """
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s in scorePages took %0.3f ms' % (func.func_name, (t2 - t1) * 1000.0)
        return res

    return wrapper
