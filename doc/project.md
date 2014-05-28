![logo](http://people.ubuntu.com/~l3on/goopg/logo.png)

# Requirements

Without using external tools, such as Email Clients, GMail users must be able to:

 * to encrypt and decrypt files and emails
 * sign and verify emails (both in-line and attached as described in RFC 3156)

The UI must be the GMail web interface, providing users with the Google User Experience.

# Requirements analysis

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
 * ```auto_token``` - bundled in the GMail HTML (variable GLOBALS at index 9)
 * ```gmail_message_id``` - the GMail internal message ID (known as ```X-GM-MSGID```), bundled as ClassName of messages in the HTML (starting with 'm')

Hence, get the original message is simple as get the the div.ClassName of the message and then do a XMLHttpRequest.


## PGP operations

Each PGP operation will be implemented outside the web context, in other words, implemented in the native application.


## Sending messages

Analyzing the HTML comes out that there is no (simple) way to (given a string) send a message via GMail web interface. Understanding how to do that could fit into the first risk analyzed.

Sending the message will be done in the native application, which instead could fit in the second risk, but remains the preferred choice.


# Project analysis

GMail HTML structure is compiled (or something like that), making hard to understand the HTML elements IDs and ClassNames. This makes stronger the first point described in Risk analysis.

The logical operations must be moved outside the web context as mush as possible.

## The representation of data
Data must be exchanged between contexts in JSON format. The main package has a event-message structure as described below:
```
package
{
    event: 'str' // the event name (sign, verify, encrypt, decrypt, import, config [set, get])
    data:  {}    // the info as obj
}
```


## The web extension
### Structure
```
main:
    void  watchForPageChanges()
    void  sendMessage()
    void  handleMessages()
page:
    div[] getMessages()
    div   getMessageById(id)
    div   getEditor()
message:
    str   getId()
    str   getOrig()
    div   getElement()
    void  setSign(gpgSign)
    void  clean()
    bool  isSigned()
    bool  isCrypted()
```

### Interaction
```
main send package to gateway
main receive package from gateway
```

### Behavior
```
main():
  while true:
    handleMessages()
    watchForPageChanges()
```
## The background
### Structure
```
gateway:
    // {p} is package
    {p}    adaptToIO({p})
    {p}    adaptToWeb({p})
    void   forwardToWeb({p})
    void   forwardToNative({p})

## future
# config: background page for Goopg configuration
```
### Interaction
```
gateway send package to main
gateway receive package from main

gateway send package to native
gateway receive package from native
```

### Behavior
```
gateway():
    while true:
        forwardToNative()
        forwardToWeb()
```

## The native application
### Structure
```
native:
    {p}   read()
    void  send({p})

gpg:
    msg   encrpyt(msg)
    msg   decrypt(msg)
    msg   verify(msg)
    msg   sign(msg)
    bool  import(key)

gmail:
    bool  connect(user, pass)
    bool  send(msg)
```

### Interaction
```
native receive package from gateway
native send package to gateway
```
### Behavior
```
native:
    gpg = gpg()
    while true:
        package = read()
        switch package.event:
        'sign':
            info = gpg.sign(package.message)
            gmail.send(msg)

        'encrypt':
            msg = gpg.encrypt(package.message)
            gmail.send(msg)

        'import':
            result = gpg.import(package.message)
            send(result)

        'verify':
            result = gpg.verify(package.message)
            send(result)

        'decrypt':
            result = gpg.decrypt(package.message)
            send(result)
```

### Test integration


# Development
## The web extension
## The gateway
## The native application

## RoadMap

 * 0.1.0 - verify signatures
 * 0.2.0 - sign messages and send them
 * 0.3.0 - decrypt messages
 * 0.4.0 - encrypt messages and send them
 * 1.0.0 - configuration
