""" Identifies best pears on the network for a particular query.
USAGE: called by mkQueryPage.py when user enters a query
"""

import re
from math import isnan

import numpy as np

from .utils import cosine_similarity, print_timing


def get_pear_data(pear):
    """ Get pear profile data """
    pear_data = []
    # Retrieve pear.profile data
    if pear.endswith('/'):
        pear = pear[:-1]

    profile = [pear]
    with open(pear + "/profile.txt") as profile_file:
        for line in profile_file:
            message = re.search('^message = (.*)', line)
            if message:
                pi_message = message.group(1)
                profile.append(pi_message)
    # web browser won't let us access local image from localhost, so using
    # generic picture
    profile.append("./static/pi-pic.png")

    return profile


@print_timing
def find_best_pears(query_dist, pear_vectors, num_best_pears=5):
    """ Finds num_best_pears pears data for query """
    best_pears_data = []

    # Calculate score for each pear in relation to the user query
    if len(query_dist) > 0:
        pears_scores = {}
        for pear_name, pear_vector in pear_vectors.items():
            score = cosine_similarity(np.array(pear_vector), query_dist)
            if not isnan(score):
                pears_scores[pear_name] = score
                print(pear_name, score)

        best_pears = [pear_name for pear_name, pear_score in
                      sorted(pears_scores.iteritems(), key=lambda x: x[1], reverse=True)[:num_best_pears]]
        best_pears_data = [get_pear_data(pear) for pear in best_pears]

    return best_pears_data
