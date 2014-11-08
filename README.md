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

# Installation:
The installation consists in two phases:
 * Install the chrome/ium extension to [this link](https://chrome.google.com/webstore/detail/goopg/ifpoaednafmgolabhpjmbimllaoidelg)
 * Install the needed packages:
```
 sudo add-apt-repository ppa:team-goopg/goopg
 sudo apt-get update
 sudo apt-get install goopg-chromium
```
 Replace `goopg-chromium` with `goopg-chrome` if you use Chrome.

Open http://gmail.com


# If you want help in develop

If you would like to help in developing, see the [dev-install](docs/dev-install.md) and the [project documentationn](docs/project.md).
