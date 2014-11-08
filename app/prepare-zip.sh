#!/bin/bash

# This files prepares the zip to upload to the Chrome Store

DIR="$( cd "$( dirname "$0" )" && pwd )"
cd $DIR

# build the css
make -C lib/ >/dev/null

# make the tmp dir
TMP_DIR=/tmp/goopg
if [ -d $TMP_DIR ]; then rm -fr $TMP_DIR ; fi
mkdir -p  $TMP_DIR/lib/css
mkdir -p  $TMP_DIR/lib/fonts

# copy the the files
cp *.js *.png *.json $TMP_DIR
for subdir in "lib/css" "lib/fonts" ; do
    cp -r "$subdir" "$TMP_DIR/lib"
done

# build the extension_id file
EXT_ID="ifpoaednafmgolabhpjmbimllaoidelg"
EXT_ID_FILE="goopg-web-extension-id.js"
TEMPLATE="../templates/$EXT_ID_FILE.in"
sed "s|@EXT_ID@|$EXT_ID|" "$TEMPLATE" > "$TMP_DIR/$EXT_ID_FILE"


# make the zip
cd $TMP_DIR
ZIP_NAME=~/goopg-chrome-store.zip
zip $ZIP_NAME `find -type f` > /dev/null

echo File $ZIP_NAME created
