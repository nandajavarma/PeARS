from textblob import Word


def lemmatiseQuery(query):
    lemmatised_query = ""
    for surface_word in query.split():
        try:
            lemma = Word(surface_word).lemmatize()
            lemmatised_query = lemmatised_query + lemma + " "
            # Hack. Now we don't have POSs anymore, we must check whether
            # the word might be an irregular verb ('was', 'would')
            lemma_verb = Word(surface_word).lemmatize('v')
            if lemma_verb != lemma:
                # Only include if different. So 'calls' (plural noun or 3.sing verb)
                # would end up with just one mention
                lemmatised_query = lemmatised_query + lemma_verb + " "
        except:
            lemmatised_query = lemmatised_query + surface_word + " "
        print lemmatised_query
    return lemmatised_query
