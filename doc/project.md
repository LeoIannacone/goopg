![logo](http://people.ubuntu.com/~l3on/goopg/logo.png)

# Requirements

Without using external tools, such as Email Clients, GMail users must be able to:

 * to encrypt and decrypt files and emails
 * sign and verify emails (both in-line and attached as described in RFC 3156)

The UI must be the GMail web interface, providing users with the Google User Experience.

## Requirements analysis

GMail web interface is not able to handle with GPG nowadays. Some other projects had tried to fix it during last years, bundling PGP algorithms in JavaScript code and heavy modifying the GMail interface.

This kind of approach seems to have failed, since GMail can suddenly change its own HTML structure, therefore making those applications useless.

A new way to look for a solution is empowering external tools which are designed to easy and quickly do PGP transformations and verifications.

According with [its developer documentation](https://developer.chrome.com/extensions/messaging), Chrome is able to make web pages communicate with native applications, hence the JavaScript running as extension may get information, pass it to the native application, which is in charge to use PGP and to apply the transformation (if needed), and get back the result.

The main contexts (draft structure and interaction):
```
web page  <-->  chrome background extension  <-->  external tool (native application)
```

The interaction between contexts (draft behavior):
```
web page           chrome background extension             external tool (native application)

get info     --->  gateway (adapt to I/O if needed)  --->  make transformation / verification
                                                                |
                                                                |
show result  <---  gateway (adapt to web if needed)  <---  send result
```


## Risks analysis

 * GMail web interface might change HTML someday. As less as possible HTML modifications and interactions could prevent future work.

 * Even if surfing the web it is enough easy to find documentation about PGP, it seems there is a lack of tool/API and example showing how emails are verified/signed/encrypted/decrypted through PGP. Understanding deeply how it works, as well as how to get and send emails, can heavy delay the development.


## Getting the original message

The web interface provides a simple way to retrieve the original email content, just opening URI like:

```
https://mail.google.com/mail/u/0/?ui=2&ik=%(auth_token)s&view=om&th=%(gmail_message_id)s
```
With:
 * `auto_token` - bundled in the GMail HTML (variable GLOBALS at index 9)
 * `gmail_message_id``` - the GMail internal message ID (known as ```X-GM-MSGID`), bundled as ClassName of messages in the HTML (starting with 'm')

Hence, get the `X-GM-MSGID` is simple as get the the div.ClassName.


## PGP operations

Each PGP operation will be implemented outside the web context, in other words, implemented in the native application.


## Sending messages

Analyzing the HTML comes out that there is no (simple) way to (given a string) send a message via GMail web interface. Understanding how to do that could fit into the first risk analyzed.

Sending the message will be done in the native application, which instead could fit in the second risk, but remains the preferred choice.


# Project analysis and development

GMail HTML structure is compiled (or something like that), making hard to understand the HTML elements IDs and ClassNames. This makes stronger the first point described in Risk analysis.

The logical operations must be moved outside the web context as mush as possible.

## The representation of data
Data must be exchanged between contexts in JSON format. The main package (called bundle) has a event-message structure as described below:
```
bundle
{
    command: 'str'       // the command name (init, sign, verify, encrypt,
                         // decrypt, import, config [set, get])
    force:  true|false   // force the command to be excecuted
    id: 'str'            // the X-GM-MSGID
    result: {}           // depends on the command result, it comes from the
                         // Host and it may be as simple as a boolean
}
```


## The web extension, the app directory
### Structure

 * `manifest.json`: the manifest of the extension (see [the official doc](https://developer.chrome.com/extensions/manifest))

 * `lib/*`: contains the css and fonts used in web (it uses [bootstrap](http://getbootstrap.com/))

 * `inject.js`: injects javascripts (goopg-web*.js) files in GMail web page

 * `goopg.js`: is the background script which takes the bundles from the web pages and forwards them to then native Host, and viceversa. It is the Gateway we talked about before and it will be described below.

 * `goopg-web-extension-id.js`: exposes the EXTENSION_ID (this is needed to easing the development)

 * `goopg-web.js`: the main javascript
 ```
  // main functions
  look_for_compositors(): on HTML change, looks for GMail compositors and
                          adds a 'Sign and Send' button
  look_for_signedmessages: on HTML change, looks for messages and sends
                           a `verify` command

  // main objects
  Utils: contain some utils
  Alert: is the banner added to the verified messages
  Port: is the port communication to send and receive bundles
  SingedMessage: represents a GMail signed message in the current view of the web page
  SingSendButton: represent a 'Sing and Send' button of the compositors
 ```


### Interaction
```
web_page send bundle to gateway
web_page receive bundle from gateway
```

### Behavior
```
html.onChange():
    look_for_compositors()
    look_for_signedmessages()
```

## The gateway/background
### Structure

 * `app/goopg.js`: creates the web-port and py-port and forwards bundles between them.

### Interaction
```
gateway send bundle to web_page
gateway receive bundle from web_page

web_page send bundle to native
web_page receive bundle from native
```

### Behavior
```
py_port.onMessage(bundle):
    web_port.postMessage(bundle)

web_port.onMessage(bundle):
    py_port.postMessage(bundle)
```

## The native application, the host directory
The native application is placed in host directory and it is written in python.

### Structure

 * `chrome-main.py```: it is the main script executed by the browser. It reads from stdin the `bundle` sent by the gateway and writes to stdout a new `bundle` as the result of the operation. It calls CommandHandler to consume the ```bundle`.

 * `commandhandler.py`: contains a class which takes care to parse the `bundle` and generates the result to send back. It calls GPGMail and GMail classes to operate with messages. In the future in may call a ConfigurationParses to properly initalize the rest of the script

 * `gpgmail.py`: contains the main functions to verify and sign a email message, it uses [gnupg.GPG](https://pythonhosted.org/python-gnupg/)

 * `gmail/__init__.py`: this is the file which contains the [GMail API](https://developers.google.com/gmail/api) calls. The code is super documented, for more info take a look inside.
 ```
  - get(id): get a the message by id

  - get_headers(id): get the headers of a message

  - message_matches(id, query): check if message matches the given query

  - send(id, message): sends a message. For now it uses a SMTP connection.
                       GMail APIs no work properly with signed messages as
                       defined in RFC 3156, therefore the `id` is not used.
 ```
 * `gmail/client_secret.json`: contains the identification of Goopg, required during the login process

### Interaction
```
native receive bundle from gateway
native send bundle to gateway
```

### Behavior
```
chrome-main.py:
    while true:
        bundle = read_from_stdin()
        result = commandhanlder.parse(bundle)
        write_to_stdout(result)
```

### Test integration
Some tests can be found in `host/tests/` directory.


# RoadMap

 * verify signatures (done)
 * sign messages and send them (done)
 * decrypt messages
 * encrypt messages and send them
 * configuration
