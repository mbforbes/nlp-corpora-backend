#!/bin/bash

#
# Run the backend crawling script, write results to main repo README,
# push update of main repo to github.
#
# This script only needs to be run by one person, so it's configured
# for a particular directory structure.
#

# setup
source ~/.bashrc
export GIT_SSH_COMMAND='ssh -i ~/.ssh/robot_id_rsa'

# setup 1: update self (ensure running latest version of backend)
cd ~/repos/nlp-corpora-backend/
git pull --rebase origin master

# step 2: run crawler
pyenv activate nlp-corpora
python check.py > ~/repos/nlp-corpora/README.md
pyenv deactivate

# setp 3: push updated doc
cd ~/repos/nlp-corpora/
git add .
git commit -m "update `date '+%m/%d/%Y %H:%M:%S'`"
git push origin master
