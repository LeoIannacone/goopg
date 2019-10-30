#!/bin/bash

set -e

usage() {
  echo "usage: ${0##*/} extension_id [chromium|google-chrome]"
  exit 1
}

EXT_ID=$1
BROWSER=$2

DIR="$( cd "$( dirname "$0" )" && pwd )"

if [ "$BROWSER" = "" ] ; then
  BROWSER="chromium"
fi

if [ "$BROWSER" != "chromium" -a "$BROWSER" != "google-chrome" ] ; then
  usage
fi

if [ "$EXT_ID" = "" ]; then
  usage
fi

if [ "$TARGET_DIR" = "" ] ; then
  TARGET_DIR="$HOME/.config/$BROWSER/NativeMessagingHosts"
fi

if [ "$HOST_PATH" = "" ] ; then
  HOST_PATH=$(realpath "$DIR/../host")
fi

# Create directory to store native messaging host.
mkdir -p "$TARGET_DIR"

# Copy native messaging host manifest.
JSON="com.leoiannacone.goopg.json"
cp "$DIR/$JSON.in" "$TARGET_DIR/$JSON"

# Update host path in the manifest.
HOST_PATH="$HOST_PATH/chrome-main.py"
sed -i '' "s|@HOST_PATH@|$HOST_PATH|" "$TARGET_DIR/$JSON"
sed -i '' "s|@EXT_ID@|$EXT_ID|" "$TARGET_DIR/$JSON"

# Set permissions for the manifest so that all users can read it.
chmod o+r "$TARGET_DIR/$JSON"

echo Native messaging host $JSON has been installed. "$TARGET_DIR/$JSON"
# make the goopg-web-extension-id
JS=goopg-web-extension-id.js
sed "s|@EXT_ID@|$EXT_ID|" "$DIR/$JS.in" > "$DIR/../app/$JS"
