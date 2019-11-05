# Install in Mac #

Goopg should work in you Mac too.

What you have to do to get it properly installed is:

1. Install the extension from the [Chrome Store](https://chrome.google.com/webstore/detail/goopg/ifpoaednafmgolabhpjmbimllaoidelg)

2. Install these python libraries:
 ```
 python-googleapi python-gflags python-xdg python-gnupg
```
3. Install coreutils via homebrew (provides `realpath`)
```
brew install coreutils
```

4. Clone this repository:
 ```
 git clone https://github.com/LeoIannacone/goopg/
 ```
 Save it somewhere because you will need this files and you cannot remove them.

5. Then install the plugin using this command in the goopg directory:
 ```
 export TARGET_DIR=~/NativeMessagingHosts
 bash templates/build-mac.sh ifpoaednafmgolabhpjmbimllaoidelg chrome
 ```
