"use strict";

// get the username
var USERNAME = GLOBALS[10];


// my css classes
var GOOPG_CLASS_PREFIX = "goopg-";
var GOOPG_CLASS_CHECKED = GOOPG_CLASS_PREFIX + "checked";
var GOOPG_CLASS_STDERR = GOOPG_CLASS_PREFIX + "stderr";
var GOOPG_CLASS_SENDBUTTON = GOOPG_CLASS_PREFIX + "sendbutton";
var GOOPG_CLASS_ALERT = GOOPG_CLASS_PREFIX + "alert";


// google css classes
var GOOGLE_CLASS_MESSAGE = "ii";
var GOOGLE_CLASS_SENDBUTTON = "aoO";
var GOOGLE_CLASS_DISCARD_BUTTON = 'og';
var GOOGLE_CLASS_ALERT = 'vh';
var GOOGLE_CLASS_MESSAGE_SAVED = 'aOy';


// port to communicate with background
var web_port = null;


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
        var goopgExtensionId = "ppopiamobkilibbniemlecehjmbfbjjp";
        window.console.log("Connecting to web port...");

        var port = window.chrome.runtime.connect(goopgExtensionId);

        port.onDisconnect.addListener(function () {
            window.console.log("Failed to connect: " + window.chrome.runtime.lastError.message);
        });

        port.onMessage.addListener(Port.handler);

        return port;
    },

    // send a msg
    send: function (msg) {
        try {
            web_port.postMessage(msg);
        } catch (err) {
            web_port = Port.get();
            web_port.postMessage(msg);
        }
    },

    // the handler
    handler: function (msg) {
        // handle the message received
        if (msg.command == 'request_init') {
            var init_command = {};
            init_command.command = 'init';
            init_command.options = {};
            init_command.options.username = USERNAME;
            Port.send(init_command);
        } else if (msg.command == "verify") {
            if (msg.result.status === null)
                return;
            var div = document.getElementsByClassName("m" + msg.id)[0];
            if (div === null)
                return;
            SignedMessage.hide_signature(msg.result.filename, div);
            div.insertBefore(SignedMessage.get_banner(msg.result), div.firstChild);
        } else if (msg.command == "sign") {
            if (msg.result === false) {
                Alert.set("Your message was not sent. Please retry.");
                var button = document.getElementById(msg.button_id);
                if (button) {
                    button.addEventListener('click', SignSendButton.on_click);
                    button.style.color = "";
                    button.innerHTML = "Sign and Send";
                }
            } else if (msg.result === true)
                SignSendButton.hide_compositor(msg.button_id);
        }
    }
};


var SignedMessage = {
    // hide signature
    hide_signature: function (filename, div) {
        if (filename === null) {
            // try to hide inline signature
            var body = div.firstChild.innerHTML;
            var info = body.split(/^-+BEGIN PGP SIGNED MESSAGE-+.*\n.*\n<br>\n+/m);
            info = info[info.length - 1];
            info = info.split(/^-+BEGIN PGP SIGNATURE-+<br>\n/m)[0];
            if (info.length != div.firstChild.innerHTML.length) {
                div.firstChild.innerHTML = info;
                return true;
            }
        } else {
            // here only if signature is attached
            var spans = div.parentElement.getElementsByTagName("span");
            for (var i = 0; i < spans.length; i++) {
                var span = spans[i];
                var download_url = span.getAttribute("download_url");
                if (download_url &&
                    download_url.indexOf("text/plain:" + filename) === 0) {
                    // this is the sign attachment
                    span.style.display = "none";
                    if (span.parentElement.children.length == 2) {
                        // only one attachment, hide the whole box
                        span.parentElement.parentElement.style.display = "none";
                    }
                    return true;
                }
            }
        }
        return false;
    },
    // build the banner
    get_banner: function (msg) {
        var className;
        var text;
        var icon;
        if (msg.status === null)
            return;
        var key_id = msg.key_id;
        if (key_id.length > 8)
            key_id = msg.key_id.substring(8);
        text = msg.username + " " + key_id;
        if (msg.status == "no public key") {
            icon = "question-sign";
            className = "warning";
            text = "public key " + key_id + " not found";
        } else if (msg.status == "signature valid" || msg.status == "signature good") {
            icon = "ok-sign";
            className = "success";
        } else { // (msg.status == "signature bad")
            icon = "exclamation-sign";
            className = "danger";
        }
        // clean stderr
        var result = document.createElement("div");
        result.className = "goopg";
        var alert = document.createElement("div");
        alert.className = "alert alert-" + className;
        var alert_header = document.createElement("div");
        alert_header.className = "alert-header";
        alert_header.innerHTML =
            "<span class=\"pull-right glyphicon glyphicon-" + icon + "\"></span>" +
            "<strong>" + Utils.capitalize(msg.status) + ":</strong> " + Utils.escape_html(text);
        alert.appendChild(alert_header);
        if (msg.stderr) {
            var stderr = msg.stderr.replace(/^.GNUPG:.*\n?/mg, "");
            alert_header.addEventListener("click", function () {
                Utils.toggle_display(this.parentElement.getElementsByClassName(GOOPG_CLASS_STDERR)[0]);
            });
            var alert_stderr = document.createElement("div");
            alert_stderr.className = "raw " + GOOPG_CLASS_STDERR;
            alert_stderr.style.display = "none";
            alert_stderr.innerHTML = Utils.escape_html(stderr);
            alert.appendChild(alert_stderr);
        }

        result.appendChild(alert);
        return result;
    },
};



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
            var msg = {};
            msg.command = "verify";
            msg.id = id;
            Port.send(msg);
        }
    }
}

function look_for_compositors() {
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

document.body.addEventListener("DOMSubtreeModified", look_for_signedmessages, false);
document.body.addEventListener("DOMSubtreeModified", look_for_compositors, false);
