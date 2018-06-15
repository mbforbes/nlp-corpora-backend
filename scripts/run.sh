#!/bin/bash

#
# Run the backend crawling script, write results to main repo README, push
# update of main repo to github.
#

python check.py --directory test/ > ~/repos/nlp-corpora/README.md
cd ~/repos/nlp-corpora/
git add .
git commit -m "update `date '+%m/%d/%Y %H:%M:%S'`"
git push origin master
