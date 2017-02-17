""" Make user profiles by adding document vectors """

import os
import sys, getpass

import numpy as np
from scipy.spatial import distance
from pears.models import Urls
import runDistSemWeighted
from pears.utils import normalise, cosine_similarity, sim_to_matrix
from pears import db
from pears.models import Profile

num_dimensions = 400

def coherence(vecs):
    coh = 0.0
    counter = 0
    if len(vecs) > 1:
        matrix = np.array(vecs)
        # print matrix
        dist_m = distance.cdist(matrix, matrix, 'cosine')
        # print dist_m
        for i in range(0, len(vecs) - 1):
            for j in range(i + 1, len(vecs)):
                cosine = 1 - dist_m[i][j]
                # print cosine
                coh += cosine
                counter += 1
        coh = float(coh) / float(counter)
    else:
        coh = 1
    # print coh
    return coh


def computePearDist():
    vbase = np.zeros(num_dimensions)
    vecs_for_coh = []  # Store vectors for this user in order to compute coherence
    # Open document distributions file
    urls = Urls.query.all()
    for l in urls:
        doc_dist = filter(None, l.dists.split(' '))
        vdocdist = np.array([float(i) for i in doc_dist])
        vbase = vbase + vdocdist
        if np.linalg.norm(vdocdist) > 0.0:
            vecs_for_coh.append(vdocdist)

    vbase = normalise(vbase)
    # Make string version of distribution
    dist_str = ""
    for n in vbase:
        dist_str = dist_str + "%.6f" % n + " "
    dist_str = dist_str.rstrip(' ')

    # coh=0
    coh = coherence(vecs_for_coh)
    # print coh
    return vbase, dist_str, coh


def createProfile(profile, pear_dist, topics_s, coh):
    profile.topics = topics_s
    profile.coherence = str(coh)
    profile.vector = pear_dist
    db.session.add(profile)
    db.session.commit()


def runScript():
    print "Computing pear for local history..."
    profile = Profile.query.first()
    if not profile:
        user = getpass.getuser()
        profile = Profile(name=unicode(user))
    v, print_v, coh = computePearDist()
    topics, topics_s = sim_to_matrix(v, 20)
    createProfile(profile, print_v, topics_s, coh)


# PERHAPS PEAR NOT FOUND?

if __name__ == '__main__':
    # when executing as script
    runScript()
