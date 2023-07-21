#!/usr/bin/env bash

./build.sh

docker save testsubmission | gzip -c > TestSubmission.tar.gz
