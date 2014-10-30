"use strict";

var USERNAME = GLOBALS[10];

var GOOPG_CLASS_PREFIX = "goopg-";
var GOOPG_CLASS_CHECKED = GOOPG_CLASS_PREFIX + "checked";
var GOOPG_CLASS_STDERR = GOOPG_CLASS_PREFIX + "stderr";
var GOOPG_CLASS_SENDBUTTON = GOOPG_CLASS_PREFIX + "sendbutton";

var GOOGLE_CLASS_MESSAGE = "ii";
//var GOOGLE_CLASS_CONTROLS = "IZ";
var GOOGLE_CLASS_SENDBUTTON = "aoO";
var GOOGLE_CLASS_DISCARD_BUTTON = 'og';
var GOOGLE_CLASS_DISCARD_ALERTMSG = 'vh';

String.prototype.capitalize = function () {
    return this.replace(/(?:^|\s)\S/g, function (a) {
        return a.toUpperCase();
    });
};

var Utils = {

    escapeHtml: function (string) {
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

    toggleDisplay: function (div) {
        if (div.style.display == "none")
            div.style.display = "block";
        else
            div.style.display = "none";
    },

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

    build_alert: function (msg) {
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
            "<span class=\"pull-right glyphicon glyphicon glyphicon-" + icon + "\"></span>" +
            "<strong>" + msg.status.capitalize() + ":</strong> " + Utils.escapeHtml(text);
        alert.appendChild(alert_header);
        if (msg.stderr) {
            var stderr = msg.stderr.replace(/^.GNUPG:.*\n?/mg, "");
            alert_header.addEventListener("click", function () {
                Utils.toggleDisplay(this.parentElement.getElementsByClassName(GOOPG_CLASS_STDERR)[0]);
            });
            var alert_stderr = document.createElement("div");
            alert_stderr.className = "raw " + GOOPG_CLASS_STDERR;
            alert_stderr.style.display = "none";
            alert_stderr.innerHTML = Utils.escapeHtml(stderr);
            alert.appendChild(alert_stderr);
        }

        result.appendChild(alert);
        return result;
    },

    build_sendbutton: function () {
        var new_button = document.createElement('div');
        new_button.className = GOOPG_CLASS_SENDBUTTON;
        new_button.id += GOOPG_CLASS_PREFIX + Math.random();
        //new_button.className += ' T-I-JW';
        new_button.innerHTML = 'Sign and Send';
        return new_button;
    },

    change_discard_alert: function () {
        var alert = document.getElementsByClassName(GOOGLE_CLASS_DISCARD_ALERTMSG)[0];

        function changer(e) {
            alert.innerHTML = "Your message has been signed and sent.";
            alert.removeEventListener(e.type, changer);
        }
        alert.addEventListener("DOMSubtreeModified", changer);
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
                Utils.change_discard_alert();
                discard.click();
                break;
            }
        }

    }

};



var web_port = null;

function get_web_port() {

    var goopgExtensionId = "ppopiamobkilibbniemlecehjmbfbjjp";
    window.console.log("Connecting to web port...");
    var port = window.chrome.runtime.connect(goopgExtensionId);

    port.onDisconnect.addListener(function () {
        window.console.log("Failed to connect: " + window.chrome.runtime.lastError.message);
    });

    port.onMessage.addListener(function (msg) {
        window.console.log("Received", msg);
        // handl the message received
        if (msg.command == 'request_init') {
            send_message_web_port(get_init_command());
        } else if (msg.command == "verify") {
            if (msg.result.status === null)
                return;
            var div = document.getElementsByClassName("m" + msg.id)[0];
            Utils.hide_signature(msg.result.filename, div);
            div.insertBefore(Utils.build_alert(msg.result), div.firstChild);
        } else if (msg.command == "sign") {
            if (msg.result === false)
                return;
            Utils.hide_compositor(msg.button_id);
        }
    });

    return port;
}

function get_init_command() {
    var init_command = {};
    init_command.command = 'init';
    init_command.options = {};
    init_command.options.username = USERNAME;
    return init_command;
}

function send_message_web_port(message) {
    try {
        web_port.postMessage(message);
    } catch (err) {
        web_port = get_web_port();
        web_port.postMessage(message);
    }
}

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
            var info = {};
            info.command = "verify";
            info.id = id;
            send_message_web_port(info);
        }
    }
}

function on_click_sendsignbutton() {
    var e = this;
    // get the message id, in html: <input name="draft" value="MSG_ID" />
    while (e.parentElement) {
        e = e.parentElement;
        var inputs = e.getElementsByTagName('input');
        for (var j = 0; j < inputs.length; j++) {
            var input = inputs[j];
            if (input.getAttribute('name') == "draft") {
                var info = {};
                info.command = "sign";
                info.id = input.getAttribute('value');
                info.button_id = this.id;
                send_message_web_port(info);
                //console.log(info)
                return;
            }
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
        var new_button = Utils.build_sendbutton(button);
        new_button.addEventListener("click", on_click_sendsignbutton);
        parent.appendChild(new_button);
    }
}

document.body.addEventListener("DOMSubtreeModified", look_for_signedmessages, false);
document.body.addEventListener("DOMSubtreeModified", look_for_compositors, false);
