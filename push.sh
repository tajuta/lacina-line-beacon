#!/bin/bash
ssh-agent -s
ssh-add ~/.ssh/id_rsa_20200420
git push $1 $2
