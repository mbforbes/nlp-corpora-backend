#!/bin/bash

#
# Run the backend crawling script, write results to main repo README,
# push update of main repo to github.
#
# This script only needs to be run by one person, so it's configured
# for a particular directory structure.
#

# step 1: run crawler
cd ~/repos/nlp-corpora-backend/
source ~/.bashrc
pyenv activate nlp-corpora
python check.py > ~/repos/nlp-corpora/README.md
pyenv deactivate

# setp 2: push updated doc
cd ~/repos/nlp-corpora/
export GIT_SSH_COMMAND='ssh -i ~/.ssh/robot_id_rsa'
git add .
git commit -m "update `date '+%m/%d/%Y %H:%M:%S'`"
git push origin master
