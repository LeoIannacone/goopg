# Installation for developers

### Deps
Install these dependencies:
```bash
sudo apt-get install node-less python-googleapi python-gflags python-xdg python-gnupg
```

### Build the css
If your distribution ships the `libjs-bootstrap` package, install it! (otherwise bootstrap will be downloaded):

```bash
cd app/lib
make
cd -
```

### Install the extension in Chrome/Chromium
* Open [chrome://extensions](chrome://extensions) in the browser
* Click on "Developer mode"
* Then click on "Load unpackaged extension" and select the dir `app`


### Update the app ID and install the host
Once extension is installed, get the `NEW_ID` extension in chrome://extension and run the following commands:
```bash
cd templates
NEW_ID=the_id_you_found
BROWSER=your_browser # (chrome or chromium)
bash build.sh $NEW_ID $BROWSER
cd -
```
Reload http://gmail.com



# About logging

For log information, see the ```~/.cache/goopg/log file```
