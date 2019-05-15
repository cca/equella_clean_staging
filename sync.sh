#!/usr/bin/env bash
# sync relevant files to EQUELLA app nodes
rsync -avz config.json clean.py data v2:~/clean-staging
rsync -avz config.json clean.py data v1:~/clean-staging
