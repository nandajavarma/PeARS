"""PeARS indexer

Usage:
indexer.py (--history=10|--file=NAME) [--cluster --cache]
indexer.py --version

Options:
-h --help     Show this screen.
--version     Show version.
--history=NUM Number of pages of local history to index
--file=NAME   Name of url file to index
--cluster     Show page clusters so user can choose what to share
--cache       Cache the text of each indexed page for offline browsing
"""

from pears.indexer import retrieve_raw_data,hierarchClustering,mkLocalProfile,clean
from docopt import docopt
import os, sys


if __name__=="__main__":
  args = docopt(__doc__, version='PeARS indexer 0.1')
  if args["--history"]:
    if args["--cache"]:
      retrieve_raw_data.runScript("history", args["--history"], "cache")
    else:
      retrieve_raw_data.runScript("history", args["--history"])
    if args["--cluster"]:
      hierarchClustering.runScript(0.7)
  if args["--file"]:
    if args["--cache"]:
      retrieve_raw_data.runScript("file", args["--file"], "cache")
    else:
      retrieve_raw_data.runScript("file", args["--file"])
    if args["--cluster"]:
      hierarchClustering.runScript(0.7)

  mkLocalProfile.runScript()
  clean.runScript()
