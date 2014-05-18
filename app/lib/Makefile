#!/bin/bash

VER="3.1.1"

# clean
rm -r fonts 2>/dev/null

# get boostrap source
curl -L -o bootstrap.tar.gz https://github.com/twbs/bootstrap/archive/v${VER}.tar.gz
tar xvzf bootstrap.tar.gz
mv bootstrap-${VER}/ bootstrap

# build css
mkdir css
lessc goopg-bootstrap.less -o css/goopg-bootstrap.css

# copy what we need
mv bootstrap/fonts/ .

# delete what we don't
rm -fr bootstrap*
