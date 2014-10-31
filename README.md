# Deps #

```bash
sudo apt-get install node-less python-googleapi python-xdg python-gnupg
```

# Build the css #
```bash
cd app/lib
bash Makefile
cd -
```

# Install in Chrome #
* Open [chrome://extensions](chrome://extensions) in the browser
* Install `unpackaged extension` (directory is `app`)

# Update the app ID #
Once extension is installed, get the `NEW_ID` extension in chrome://extension and run:
```bash
NEW_ID=the_id_you_found
OLD_ID=ppopiamobkilibbniemlecehjmbfbjjp
sed s/$OLD_ID/$NEW_ID/ -i `grep -r $OLD_ID | cut -d':' -f1`
```

# Install the host
```bash
cd host
bash install.sh
cd -
```

Open http://gmail.com