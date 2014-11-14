"use strict";

// get the username
var USERNAME = GLOBALS[10];


// my css classes
var GOOPG_CLASS_BANNER = "goopg";
var GOOPG_CLASS_PREFIX = "goopg-";
var GOOPG_CLASS_CHECKED = GOOPG_CLASS_PREFIX + "checked";
var GOOPG_CLASS_STDERR = GOOPG_CLASS_PREFIX + "stderr";
var GOOPG_CLASS_SENDBUTTON = GOOPG_CLASS_PREFIX + "sendbutton";
var GOOPG_CLASS_ALERT = GOOPG_CLASS_PREFIX + "alert";
var GOOPG_CLASS_KEYID = GOOPG_CLASS_PREFIX + "keyid-";
var GOOPG_CLASS_IMPORT = GOOPG_CLASS_PREFIX + "import-";
var GOOPG_CLASS_MSG_SIGNINLINE = GOOPG_CLASS_PREFIX + 'signinline';


// google css classes
var GOOGLE_CLASS_MESSAGE = "ii";
var GOOGLE_CLASS_SENDBUTTON = "aoO";
var GOOGLE_CLASS_DISCARD_BUTTON = 'og';
var GOOGLE_CLASS_ALERT = 'vh';
var GOOGLE_CLASS_MESSAGE_SAVED = 'aOy';


// port to communicate with background
var web_port = null;

// if cannot comunicate with the py port
var native_available = true;


var Utils = {

    escape_html: function (string) {
        return String(string).replace(/[&<>"'\/]/g, function (s) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                "\"": "&quot;",
                "'": "&#39;",
                "/": "&#x2F;"
            }[s];
        });
    },

    toggle_display: function (div) {
        if (div.style.display == "none")
            div.style.display = "block";
        else
            div.style.display = "none";
    },

    capitalize: function (str) {
        return str.replace(/(?:^|\s)\S/g, function (a) {
            return a.toUpperCase();
        });
    },

    get_init_bundle: function () {
        var bundle = {};
        bundle.command = 'init';
        bundle.options = {};
        bundle.options.username = USERNAME;
        return bundle;
    }
};


var Alert = {
    // set an alert msg
    set: function (msg) {
        var alert = document.getElementsByClassName(GOOGLE_CLASS_ALERT)[0];
        var random_id = GOOPG_CLASS_ALERT + Math.random();
        alert.innerHTML = '<span id="' + random_id + '">' + msg + '</span>';
        // show the alert ; gmail hides this by setting top = -10000px over this container
        var alert_container = alert.parentElement.parentElement;
        alert_container.style.top = '0px';
        // remove the alert after 15 s if still present
        setTimeout(function () {
            var this_alert = document.getElementById(random_id);
            if (this_alert) {
                var parent = this_alert.parentElement;
                parent.removeChild(this_alert);
                // revert
                if (parent.children.length === 0) {
                    alert_container.style.top = "-10000px";
                }

            }
        }, 15000);
    },

    // replace the next message with a new one
    replace_incoming_msg: function (new_msg) {
        var alert = document.getElementsByClassName(GOOGLE_CLASS_ALERT)[0];

        function changer(e) {
            alert.removeEventListener(e.type, changer);
            alert.innerHTML = new_msg;
        }
        alert.addEventListener("DOMSubtreeModified", changer);
    }
};


var Port = {
    // return a new port
    get: function () {
        window.console.log("Connecting to web port...");

        var port = window.chrome.runtime.connect(GOOPG_EXTENSION_ID);

        port.onDisconnect.addListener(function () {
            window.console.log("Failed to connect: " + window.chrome.runtime.lastError.message);
        });

        port.onMessage.addListener(Port.handler);

        return port;
    },

    // send a bundle
    send: function (bundle) {
        try {
            web_port.postMessage(bundle);
        } catch (err) {
            web_port = Port.get();
            web_port.postMessage(bundle);
        }
    },

    // the handler
    handler: function (bundle) {
        // handle the message received
        if (bundle.command == 'request_init') {
            var init_bundle = Utils.get_init_bundle();
            Port.send(init_bundle);
        } else if (bundle.command == "verify") {
            if (bundle.result.status === null)
                return;
            var signedmessage = new SignedMessage(bundle.id);
            if (signedmessage.exists()) {
                signedmessage.hide_signature(bundle.result.filename);
                signedmessage.add_banner(bundle.result);
            }
        } else if (bundle.command == "sign") {
            if (bundle.result === true) {
                SignSendButton.hide_compositor(bundle.button_id);
            } else if (bundle.result === false) {
                Alert.set("Your message was not sent. Please retry.");
                var button = document.getElementById(bundle.button_id);
                if (button) {
                    button.addEventListener('click', SignSendButton.on_click);
                    button.style.color = "";
                    button.innerHTML = "Sign and Send";
                }
            }
        } else if (bundle.command == "import") {
            if (bundle.result === true) {
                var messages = document.getElementsByClassName(GOOPG_CLASS_KEYID + bundle.id);
                for (var i = 0; i < messages.length; i++) {
                    var message = messages[i];
                    for (var j = 0; j < message.classList.length; j++) {
                        if (message.classList[j].length > 5 && message.classList[j][0] == "m") {
                            var id = message.classList[j].substring(1);
                            var bundle_verify = {};
                            bundle_verify.command = "verify";
                            bundle_verify.force = true;
                            bundle_verify.id = id;
                            Port.send(bundle_verify);
                            break;
                        }
                    }
                }
            }
        } else if (bundle.port_error) {
            var message = bundle.port_error;
            if (message == 'Access to the specified native messaging host is forbidden.' ||
                message == 'Specified native messaging host not found.') {
                native_available = false;
                setTimeout(function () {
                    var installation = 'Please see the <span><a href="http://leoiannacone.github.io/goopg/">installation</a></span> instructions.';
                    Alert.set('Goopg cannot communicate with the plugin. ' + message + ' ' + installation);
                }, 5000);
            }
        }
    }
};


function SignedMessage(msg_id) {

    this.msg_id = msg_id;
    this.key_id = null;
    this.div = document.getElementsByClassName("m" + msg_id)[0];

    this.exists = function () {
        return this.div !== null && this.div !== undefined;
    };

    // hide signature
    this.hide_signature = function (filename) {
        function get_sign_inline_hook(text) {
            return '<pre class="' + GOOPG_CLASS_MSG_SIGNINLINE + '">' + text + '</pre>';
        }
        if (!this.exists())
            return;
        if (filename === undefined) {
            // Signature inline, try to hide it
            var body = this.div.firstChild.innerHTML;
            // stricty_reg to check PGP signed inline with HTML trailing <br> elements
            // var strinct_reg = /-----BEGIN PGP SIGNED MESSAGE-----.*\nHash.*\n.*\n((.*\n)+)-----BEGIN PGP SIGNATURE-----(.*\n)+-----END PGP SIGNATURE-----.*\n/m;
            // permissive_reg is a strinct_reg which allows any HTML code before the PGP signature (need tests)
            var permissive_reg = /-----BEGIN PGP SIGNED MESSAGE-----.*\n.*Hash.*\n.*\n((.*\n)+).*-----BEGIN PGP SIGNATURE-----(.*\n)+.*-----END PGP SIGNATURE-----.*\n/m;
            var reg = permissive_reg;
            if (reg.test(body)) {
                var header = get_sign_inline_hook('-----BEGIN PGP SIGNED MESSAGE INLINE-----');
                var footer = get_sign_inline_hook('-----END PGP SIGNED MESSAGE INLINE-----');
                this.div.firstChild.innerHTML = body.replace(reg, header + ' $1 ' + footer);
            }
        } else {
            // Here only if signature is attached
            // If the signature is attached with no name,
            // gmail will show it as a 'noname' attachment, so set ...
            if (filename === null)
                filename = 'noname';
            this.hide_attachment(filename);
        }
    };

    // get the attachments as HTML elements
    this.get_attachments = function () {
        return this.div.parentElement.getElementsByTagName("span");
    };

    // get the attchment as HTML element
    this.get_attachment = function (filename) {
        var attachments = this.get_attachments();
        var url_regex = new RegExp(':' + filename + ':https://mail.google.com/');
        for (var i = 0; i < attachments.length; i++) {
            var attach = attachments[i];
            var download_url = attach.getAttribute("download_url");
            if (download_url && download_url.match(url_regex)) {
                return attach;
            }
        }
        return null;
    };

    // hide an attachment given a filename
    this.hide_attachment = function (filename) {
        var attach = this.get_attachment(filename);
        if (attach === null)
            return false;

        attach.style.display = "none";
        if (attach.parentElement.children.length == 2) {
            // it was only one attachment, hide the whole attachments box
            attach.parentElement.parentElement.style.display = "none";
        }
        return true;
    };

    // build the banner
    this.add_banner = function (gpg, force) {
        if (!this.exists())
            return;
        if (gpg.status === undefined || gpg.status === null)
            return;

        var existing_banner = this.div.getElementsByClassName(GOOPG_CLASS_BANNER);
        if (existing_banner.length == 1)
            this.div.removeChild(existing_banner[0]);

        this.key_id = gpg.key_id;

        var className;
        var icon;
        var import_key = false;

        var key_id = gpg.key_id;
        // // show the whole key and add a space every 4 chars
        // key_id = key_id.replace(/(.{4})/g, "$1 ");

        // show only last 8 chars for key id
        if (key_id.length > 8)
            key_id = key_id.substring(8);

        var text = [];

        if (gpg.username !== null)
            text.push(gpg.username);
        if (key_id)
            text.push(key_id);
        if (gpg.key_status)
            text.push("• " + gpg.key_status);

        text = text.join(' ');

        if (gpg.status == "no public key") {
            icon = "question-sign";
            className = "warning";
            text = "public key " + key_id + " not found";
            import_key = true;
        } else if (gpg.valid) {
            icon = "ok-sign";
            className = "success";
        } else { // (gpg.status == "signature bad")
            icon = "exclamation-sign";
            className = "danger";
        }

        // build the banner
        var banner = document.createElement("div");
        banner.className = "alert alert-" + className;

        var header = document.createElement("div");
        header.className = "alert-header";
        var icon_status = "<span class=\"pull-right glyphicon glyphicon-" + icon + "\"></span>";
        header.innerHTML = icon_status;
        // if import_key, add the import button
        if (import_key) {
            var icon_import = document.createElement("span");
            icon_import.className = "pull-right glyphicon glyphicon-download ";
            icon_import.className += GOOPG_CLASS_IMPORT + this.key_id;
            icon_import.title = "Import the key";
            icon_import.addEventListener("click", function (event) {
                event.stopPropagation();
                var button = event.target;
                for (var i = 0; i < button.classList.length; i++) {
                    if (button.classList[i].indexOf(GOOPG_CLASS_IMPORT) >= 0) {
                        var key_id = button.classList[i].replace(GOOPG_CLASS_IMPORT, '');
                        var bundle = {};
                        bundle.command = 'import';
                        bundle.id = key_id;
                        Port.send(bundle);
                        break;
                    }
                }
            });
            header.appendChild(icon_import);
        }
        var span_text = document.createElement('span');
        span_text.innerHTML = "<strong>" + Utils.capitalize(gpg.status) + ":</strong> " + Utils.escape_html(text);
        header.appendChild(span_text);
        banner.appendChild(header);

        if (gpg.stderr) {
            var stderr = document.createElement("div");
            var gpg_stderr_clean = gpg.stderr.replace(/^.GNUPG:.*\n?/mg, "");
            stderr.className = "raw " + GOOPG_CLASS_STDERR;
            stderr.style.display = "none";
            header.addEventListener("click", function () {
                Utils.toggle_display(this.parentElement.getElementsByClassName(GOOPG_CLASS_STDERR)[0]);
            });
            header.style.cursor = "pointer";
            stderr.innerHTML = Utils.escape_html(gpg_stderr_clean);
            banner.appendChild(stderr);
        }

        // wrap the banner
        var wrapper = document.createElement("div");
        wrapper.className = GOOPG_CLASS_BANNER;
        wrapper.appendChild(banner);
        this.div.insertBefore(wrapper, this.div.firstChild);

        var class_keyid = GOOPG_CLASS_KEYID + gpg.key_id;
        if (!this.div.classList.contains(class_keyid))
            this.div.classList.add(class_keyid);
    };
}



var SignSendButton = {
    // build the button element
    get: function () {
        var new_button = document.createElement('div');
        new_button.className = GOOPG_CLASS_SENDBUTTON;
        new_button.id += GOOPG_CLASS_PREFIX + Math.random();
        //new_button.className += ' T-I-JW';
        new_button.innerHTML = 'Sign and Send';
        return new_button;
    },

    // check if message is saved, starting from the sending button
    message_is_saved: function (button) {
        var tr = button.parentElement.parentElement.parentElement;
        return tr.getElementsByClassName(GOOGLE_CLASS_MESSAGE_SAVED).length == 1;
    },

    // get the message id wrapped around button
    get_message_id: function (button) {
        var e = button;
        // get the message id, in html: <input name="draft" value="MSG_ID" />
        while (e.parentElement) {
            e = e.parentElement;
            var inputs = e.getElementsByTagName('input');
            for (var j = 0; j < inputs.length; j++) {
                var input = inputs[j];
                if (input.getAttribute('name') == "draft") {
                    return input.getAttribute('value');
                }
            }
        }
    },

    on_click: function (event, interactions) {
        // the sending button
        var button = event.target;
        var draft_id = SignSendButton.get_message_id(button);

        if (draft_id == "undefined") {
            Alert.set("Please save the Draft before sending.");
            return;
        }
        // prevent multi click
        button.removeEventListener("click", SignSendButton.on_click);
        // stylish the button pressed
        button.style.width = window.getComputedStyle(button).width;
        button.style.color = "#999";
        button.innerHTML = "Sending";
        // If message is not saved, sleep a while (SLEEP_TIME in ms) and auto-recall
        // Do this for MAX_ITERATIONS times (?)
        var SLEEP_TIME = 500;
        var MAX_ITERATIONS = 20;
        if (interactions === undefined) {
            interactions = 0;
        }
        if (!SignSendButton.message_is_saved(button) && interactions < MAX_ITERATIONS) {
            setTimeout(function () {
                SignSendButton.on_click(event, interactions + 1);
            }, SLEEP_TIME);
            return;
        }
        var msg = {};
        msg.command = "sign";
        msg.id = draft_id;
        msg.button_id = button.id;
        Port.send(msg);
    },

    hide_compositor: function (button_id) {
        var button = document.getElementById(button_id);
        if (button === null)
            return;

        var e = button;
        while (e.parentElement) {
            e = e.parentElement;
            var discard = e.getElementsByClassName(GOOGLE_CLASS_DISCARD_BUTTON);
            if (discard.length === 0)
                continue;
            else if (discard.length > 1)
                return;
            else {
                discard = discard[0];
                Alert.replace_incoming_msg("Your message has been signed and sent. ");
                discard.click();
                break;
            }
        }
    },
};


function look_for_signedmessages() {
    if (native_available === false)
        return;
    var messages = document.getElementsByClassName(GOOGLE_CLASS_MESSAGE);
    for (var i = 0; i < messages.length; i++) {
        var id = null;
        var classList = messages[i].classList;
        if (classList.contains(GOOPG_CLASS_CHECKED))
            continue;
        for (var j = 0; j < classList.length; j++) {
            if (classList[j].length > 5 && classList[j][0] == "m") {
                id = classList[j].substring(1);
                messages[i].classList.add(GOOPG_CLASS_CHECKED);
                break;
            }
        }
        if (id) {
            var bundle = {};
            // guess if message is GPG signed inline
            var body = messages[i].innerText;
            if (body.indexOf('-----BEGIN PGP SIGNATURE-----') >= 0)
                bundle.force = true;
            // This will not work, since Gmail has not yet showed the attachments
            // this message.
            // else if (new SignedMessage(id).get_attachment('signature.asc'))
            //     bundle.force = true;
            bundle.command = "verify";
            bundle.id = id;
            Port.send(bundle);
        }
    }
}

function look_for_compositors() {
    if (native_available === false)
        return;
    var sendButtons = document.getElementsByClassName(GOOGLE_CLASS_SENDBUTTON);
    // append the sign&send button
    for (var i = 0; i < sendButtons.length; i++) {
        var button = sendButtons[i];
        var parent = button.parentNode;
        if (parent.className.indexOf(GOOPG_CLASS_CHECKED) > -1)
            continue;
        parent.className += ' ' + GOOPG_CLASS_CHECKED;
        var new_button = SignSendButton.get(button);
        new_button.addEventListener("click", SignSendButton.on_click);
        parent.appendChild(new_button);
    }
}

// initalize the native application on start
Port.send(Utils.get_init_bundle());

document.body.addEventListener("DOMSubtreeModified", look_for_signedmessages, false);
document.body.addEventListener("DOMSubtreeModified", look_for_compositors, false);
