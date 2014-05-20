"use strict";
var GOOPG_CLASS_PREFIX = "goopg-";
var GOOPG_CLASS_CHECKED = GOOPG_CLASS_PREFIX + "checked";

var GOOGLE_CLASS_MESSAGE = "ii";
var GOOGLE_CLASS_CONTROLS = "IZ";

function escapeHtml(string) {
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
}

String.prototype.capitalize = function () {
    return this.replace(/(?:^|\s)\S/g, function (a) {
        return a.toUpperCase();
    });
};

function toggleDisplay(div) {
    if (div.style.display == "none")
        div.style.display = "block";
    else
        div.style.display = "none";
}

function showGPGstdErr(div) {
    toggleDisplay(div.parentElement.getElementsByClassName("gpgStdErr")[0]);
}

function hide_signature(div, iterations) {
    if (!iterations)
        iterations = 0;
    var body = div.firstChild.innerHTML;
    try {
        // try to hide inline signature
        var info = body.split(/^-+BEGIN PGP SIGNED MESSAGE-+.*\n.*\n<br>\n+/m);
        info = info[info.length - 1];
        info = info.split(/^-+BEGIN PGP SIGNATURE-+<br>\n/m)[0];
        if (info.length != div.firstChild.innerHTML.length) {
            div.firstChild.innerHTML = info;
            return true;
        }
        throw "";
    } catch (err) {
        // here only if signature is attached
        var spans = div.parentElement.getElementsByTagName("span");
        for (var i = 0; i < spans.length; i++) {
            var span = spans[i];
            var download_url = span.getAttribute("download_url");
            if (download_url &&
                download_url.indexOf("text/plain:signature.asc") === 0) {
                // this is the sign attachment
                span.style.display = "none";
                if (span.parentElement.children.length == 2) {
                    // only one attachment, hide the whole box
                    span.parentElement.parentElement.style.display = "none";
                }
                return true;
            }
        }
        // maaaad try three times at max, then exit
        if (iterations < 3)
            setTimeout(function () {
                hide_signature(div, iterations + 1);
            }, 250);
    }
    return false;
}

function build_alert(msg) {
    var className;
    var text;
    var icon;
    if (msg.status === null)
        return;
    else if (msg.status == "no public key") {
        icon = "question-sign";
        className = "warning";
        text = "public key " + msg.stderr.match(/using .* key ID (.*)/)[1] + " not found";
    } else if (msg.status == "signature valid") {
        icon = "ok-sign";
        className = "success";
        text = msg.username + " " + msg.stderr.match(/using .* key ID (.*)/)[0];
    } else { // (msg.status == "signature bad")
        icon = "exclamation-sign";
        className = "danger";
        text = msg.username + " " + msg.stderr.match(/using .* key ID (.*)/)[0];
    }
    // clean stderr
    var stderr = msg.stderr.replace(/^.GNUPG:.*\n?/mg, "");
    var result = document.createElement("div");
    result.className = "goopg";
    result.innerHTML = "<div onclick=\"showGPGstdErr(this)\" class=\"alert alert-" + className + "\">" +
        "<span class=\"pull-right glyphicon glyphicon glyphicon-" + icon + "\"></span>" +
        "<strong>" + msg.status.capitalize() + ":</strong> " + escapeHtml(text) +
        "<div class=\"gpgStdErr raw\" style=\"display:none;\">" + escapeHtml(stderr) + "</div>" +
        "</div>";
    return result;
}



var web_port = null;

function get_web_port() {

    var goopgExtensionId = "ddlebbablilfigfkkjedbpapjichmjgd";
    window.console.log("Connecting to web port...");
    var port = window.chrome.runtime.connect(goopgExtensionId);

    port.onDisconnect.addListener(function () {
        window.console.log("Failed to connect: " + window.chrome.runtime.lastError.message);
    });

    port.onMessage.addListener(function (msg) {
        window.console.log("Received", msg);
        if (msg.status === null)
            return;
        var div = document.getElementsByClassName("m" + msg.id)[0];
        hide_signature(div);
        div.insertBefore(build_alert(msg), div.firstChild);
    });

    return port;
}

function send_message_web_port(message) {
    try {
        web_port.postMessage(message);
    } catch (err) {
        web_port = get_web_port();
        web_port.postMessage(message);
    }
}

function get_orig_message(id, callback) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
            callback(xmlHttp.responseText);
        }
    };
    var auth = window.GLOBALS[9];
    var url = "https://mail.google.com/mail/u/0/?ui=2&ik=" + auth + "&view=om&th=" + id;
    xmlHttp.open("GET", url, false);
    xmlHttp.send(null);
}

function look_for_messages() {
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
            get_orig_message(id, function (message) {
                if (message.match(/^-+BEGIN PGP SIGNATURE-+/m)) {
                    var info = {};
                    info.command = "verify";
                    info.id = id;
                    info.message = message;
                    send_message_web_port(info);
                }
            });
        }
    }
}

document.body.addEventListener("DOMSubtreeModified", look_for_messages, false);
