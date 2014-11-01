![logo.png](https://bitbucket.org/repo/on9K89/images/2089013194-logo.png)

# GPG for GMail #

# Intro #

**WARN**: This is an alpha version.

### *What you can do:* ###

* Recruit alpha-testers:

 * requirements: must be developers (or something like that)
 * how: send to l3on@ubuntu.com the bitbucket account request


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
bash Makefile
cd -
```

# Install in Chrome #
* Open [chrome://extensions](chrome://extensions) in the browser
* Click on "Developer mode"
* Then click on "Load unpackage extension" and select the dir `app`

# Update the app ID #
Once extension is installed, get the `NEW_ID` extension in chrome://extension and run:
```bash
NEW_ID=the_id_you_found
OLD_ID=ppopiamobkilibbniemlecehjmbfbjjp
sed s/$OLD_ID/$NEW_ID/ -i app/goopg-web.js host/com.leoiannacone.goopg.json
```

# Install the host

If you use chromium:
```bash
cd host
bash install.sh
cd -
```

If you use chrome:
```bash
cd host
bash install.sh google-chrome
cd -
```

Open http://gmail.com


# Knonw issues #
Force digest sign algo to SHA512 in gpg:
```bash
echo "personal-digest-preferences SHA512
cert-digest-algo SHA512
default-preference-list SHA512 SHA384 SHA256 SHA224 AES256 AES192 AES CAST5 ZLIB BZIP2 ZIP Uncompressed
" >> ~/.gnupg/gpg.conf
```