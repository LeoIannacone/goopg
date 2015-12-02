![logo.png](http://leoiannacone.github.io/goopg/images/logo.png)

Goopg is an extension for the **Chrome** and the **Chromium** browser which
enables GPG sign and verification in the Gmail web page.

# Installation:
The installation consists in two phases:
 * Install the browser extension from [this link](https://chrome.google.com/webstore/detail/goopg/ifpoaednafmgolabhpjmbimllaoidelg)
 * Install the goopg plugin:
```
 sudo add-apt-repository ppa:team-goopg/goopg
 sudo apt-get update
 sudo apt-get install goopg-chromium
```
 Replace `goopg-chromium` with `goopg-chrome` if you use Chrome.

Open http://gmail.com

# Missing gpg-agent

In case goopg is able to check signatures but unable to sign and send emails,
chances are your system lacks a properly configured gpg-agent to unlock your
private key

In this case, please check [this link](https://wiki.archlinux.org/index.php/GnuPG#gpg-agent)
and follow the instructions there to enable gpg-agent.

#### If you want help in develop

If you would like to help in developing, take a look at the [dev-install](doc/dev-install.md)
and at the [project documentation](doc/project.md).

# Donate
If you like this project, please consider a donation. See the [homepage](http://leoiannacone.github.io/goopg/)
for more info.

This project is NOT affiliated with Google.
