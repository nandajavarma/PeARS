---
layout: post
title:  "P6: Topicalising search queries"
---
It is now time to think about our actual search function. The first thing we have to do is find a way to topicalise the user's query, i.e. find out roughly what it is about. This step is the most crucial one in the whole PeARS framework: it ensures that we don't have to go and search all the pears on the network – only the relevant ones. To do this, we will use the topic.keys file we produced at [the topic modelling stage](/2014/07/15/topic-modelling/) and use [distributional semantics](http://www.jair.org/media/2934/live-2934-4846-jair.pdf) to try and match the query to the topics in the topic.keys file.

Note that this entry relates to a script, topicaliseQueryBrowser.py , available in [my repository](https://github.com/minimalparts/PeARS/). If you would like to run the code without learning about each step separately, please consult [this page]({{ site.baseurl }}/install/).

(This blog entry is part of a series starting [here](2014/07/13/retrieving-browsing-history/))

Requirements:
-------------
Install DISSECT from http://clic.cimec.unitn.it/composes/toolkit/installation.html


Procedure:
----------

In order to topicalise our query, we want to compare it to the various topics created by MALLET for the webpages we have processed. We could do it by just comparing the words in the query to the words in the topics, but that wouldn't be very clever because the topic representation only gives us a list of words that are prototypical for that topic, not all possible words related to it. If we input 'terrier' as our query, to find the corresponding breed of dogs, and our dog topic does not contain that word, we will not return any pages. A better way to do things would be to have a sytem which, when we input 'terrier', returns topics containing the word 'dog': that is, a sytem that recognises the similarity of 'terrier' and 'dog'. Fortunately, we can do this using some insights from distributional semantics.

Distributional semantics is a computational theory of meaning based on the idea that the meaning of words come from their usage; i.e. what 'dog' means is defined by the way people use the word in ordinary language. By analysing large bodies of text -- say, the whole of Wikipedia --, a computer system can thus derive mathematical representations of word meaning. Words are expressed in terms of vectors in a space,  and the distance between two words (vectors) in that space is proportional to their similarity. For those interested, there is more information about distributional semantics [here](http://www.jair.org/media/2934/live-2934-4846-jair.pdf) and [here](http://www.cl.cam.ac.uk/~sc609/pubs/sem_handbook.pdf).

The PeARS repository provides a file called wikiwoods.ppmi.nmf_300.pkl, which is the representation of 10,000 very frequent words in Wikipedia. This file, together with the DISSECT toolkit, will help us derive similarities between words in the query and words in the topic.keys file.

In the following, I assume that we have two pis on the network, Pi1 and Pi2. Pi1 has indexed Wikipedia pages, while Pi2 contains stackoverflow Q&As. We have just concatenated their topic.keys files and made the result available to the queryer:

{% highlight bash %}
mkdir query/
cd query/
cat ../Pi1/wikipedia.topic.keys ../Pi2/stackoverflow.topic.keys > topic.keys
{% endhighlight %}

Obviously, with thousands of Pis on the network, we would need a cleverer way to aggregate the topic.keys files. But for now, we will keep things simple. I have written a little python script, *topicalise-query.py*,  which asks the user to enter a query and identifies which Pi(s) are more likely to provide the answer. The output looks like this:


{% highlight bash %}
python topicalise-query.py bnc.ppmi.nmf_300.pkl
search: bald eagle
0.496709675873 Pi1: 7	1	rrb lrb moose elk deer crab red hydrangea bull gaur \
hermit okapi species duiker antler north mountain wombat forest 
0.360004187419 Pi1: 6	1	fish shark salmon species tuna pike octopus salamander \
retrieve carp trout pacific fishing fin water sea catshark atlantic freshwater 
0.345197911976 Pi1: 38	1	rrb lrb tiger mongoose cat seal badger fox otter coyote \
civet weasel hyena family genet striped fur american palm 
[['Pi1', '7'], ['Pi1', '6'], ['Pi1', '38']]

{% endhighlight %}

### A bit more information:

We need to lemmatise the query. This is a problem, as loading the stanford tagger for every query would results in unacceptable running times (loading the tagger takes around 3s on my 4GB VirtualBox). Instead of making a call to the tagger every time we need it, we will run it as a server instead:


{% highlight bash %}
nohup java -mx300m -classpath ~/stanford-postagger-2014-06-16/stanford-postagger.jar edu.stanford.nlp.tagger.maxent.MaxentTaggerServer -model ~/stanford-postagger-2014-06-16/models/english-left3words-distsim.tagger -outputFormatOptions lemmatize -outputFormat inlineXML -port 2020 >& /dev/null &
{% endhighlight %}

We can now query the server whenever we need to, and save the output to a file:

{% highlight bash %}
wget -O query.lemmas http://localhost:2020/?fish+recipes
{% endhighlight %}

The query.lemmas file looks like this:

{% highlight bash %}
<sentence id="10">
  <word wid="0" pos="VB" lemma="get">GET</word>
  <word wid="1" pos=":" lemma="/">/</word>
  <word wid="2" pos="." lemma="?">?</word>
</sentence>
<sentence id="11">
  <word wid="0" pos="NN" lemma="fish">fish</word>
  <word wid="1" pos="CC" lemma="+">+</word>
  <word wid="2" pos="NNS" lemma="recipe">recipes</word>
  <word wid="3" pos="NN" lemma="http/1">HTTP/1</word>
  <word wid="4" pos="CD" lemma=".1">.1</word>
</sentence>
{% endhighlight %}

Once we are done with the server, we can kill it like this:

{% highlight bash %}
pkill -f stanford
{% endhighlight %}

Integrating the command into our python code can cause an error: sh: Syntax error: Bad fd number. This can be fixed by changing the symbolic link from /bin/sh to /bin/bash. Do:

{% highlight bash %}
sudo mv /bin/sh /bin/sh.orig
sudo ln -s /bin/bash /bin/sh
{% endhighlight %}