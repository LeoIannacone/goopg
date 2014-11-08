# GPG for GMail #

![logo.png](http://people.ubuntu.com/~l3on/goopg/logo-50perc.png)

**WARN**: This is an alpha version.

### *What you can do:* ###

* Recruit alpha-testers:

 * requirements: must be developers (or something like that)
 * how: send to l3on@ubuntu.com the github account request


### Wath you cannot do: ###

* Share the code for now, it will be realased when ready


### What you should do: ###

* Spread screenshots about GMail is going to get new extension


# Deps #

```bash
sudo apt-get install node-less python-googleapi python-gflags python-xdg python-gnupg
```

# Build the css #
```bash
cd app/lib
make
cd -
```

# Install the extension in Chrome/Chromium #
* Open [chrome://extensions](chrome://extensions) in the browser
* Click on "Developer mode"
* Then click on "Load unpackage extension" and select the dir `app`

# Update the app ID and install the host #
Once extension is installed, get the `NEW_ID` extension in chrome://extension and run the following commmands:
```bash
cd templates
NEW_ID=the_id_you_found
BROWSER=your_browser # (chrome or chromium)
bash build.sh $NEW_ID $BROWSER
cd -
```

Open http://gmail.com
