#!/bin/bash

VER="3.1.1"

# clean
rm -r fonts 2>/dev/null

# get bootstrap source
curl -L -o bootstrap.tar.gz https://github.com/twbs/bootstrap/archive/v${VER}.tar.gz
tar xzf bootstrap.tar.gz
mv bootstrap-${VER}/ bootstrap

# build css
lessc goopg-bootstrap.less -o css/goopg-bootstrap.css

# fix font exposing
sed "s~url('../fonts/~url('chrome-extension://__MSG_@@extension_id__/lib/fonts/~g" -i css/goopg-bootstrap.css

# copy what we need
mv bootstrap/fonts/ .

# delete what we don't
rm -fr bootstrap*
