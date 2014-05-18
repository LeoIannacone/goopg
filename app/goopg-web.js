GOOPG_CLASS_PREFIX = "goopg-"
GOOPG_CLASS_CHECKED = GOOPG_CLASS_PREFIX + "checked"

function escapeHtml(string) {
    return String(string).replace(/[&<>"'\/]/g, function(s) {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': '&quot;',
            "'": '&#39;',
            "/": '&#x2F;'
        }[s];
    });
}

String.prototype.capitalize = function() {
    return this.replace(/(?:^|\s)\S/g, function(a) {
        return a.toUpperCase();
    });
};

function toggleDisplay(div) {
    if (div.style.display == "none")
        div.style.display = "block";
    else
        div.style.display = "none"
}

function showGPGstdErr(div) {
    toggleDisplay(div.parentElement.getElementsByClassName('gpgStdErr')[0])
}

function build_body(body) {
    // make urls
    var exp = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    body = body.replace(exp, "<a href='$1'>$1</a>");
    return body
}

function clean_body(body) {
    var lines = body.split('\n')
    // remove header
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i]
        if (line.indexOf('-----BEGIN PGP SIGNED MESSAGE-----') == 0) {
            j = i
            while (line != '<br>' && i < lines.length) {
                line = lines[i++]
            }
            lines.splice(j, i - j);
            break;
        }
    }
    // remove inline sign
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i]
        if (line.indexOf('-----BEGIN PGP SIGNATURE-----') == 0) {
            j = i
            while (line.indexOf('-----END PGP SIGNATURE-----') < 0 && i < lines.length) {
                line = lines[i++]
            }
            lines.splice(j, i - j);
            break;
        }
    }
    return lines.join('\n');
}

function build_alert(msg) {
    var className;
    var text;
    var extra_button = '';
    if (msg.status == null)
        return;
    else if (msg.status == "no public key") {
        className = "warning";
        text = "public key " + msg.stderr.match(/using .* key ID (.*)/)[1] + " not found"
    } else if (msg.status == "signature valid") {
        className = "success";
        text = msg.username + " " + msg.stderr.match(/using .* key ID (.*)/)[0]
    } else { // (msg.status == "signature bad")
        className = "danger";
        text = msg.username + " " + msg.stderr.match(/using .* key ID (.*)/)[0]
    }
    // clean stderr
    var stderr = msg.stderr.replace(/^.GNUPG:.*\n?/mg, '');
    var result = document.createElement('div');
    result.className = "goopg";
    result.innerHTML = '<div class="alert alert-' + className + '">' +
        '<a onclick="showGPGstdErr(this)" class="btn btn-link alert-link pull-right">' +
        '<span class="glyphicon glyphicon glyphicon-info-sign"></span></a>' +
        '<strong>' + msg.status.capitalize() + ':</strong> ' + escapeHtml(text) +
        '<div class="gpgStdErr raw" style="display:none;">' + escapeHtml(stderr) + '</div>' +
        '</div>';
    return result;
}


var goopgExtensionId = "ddlebbablilfigfkkjedbpapjichmjgd";
var port = chrome.runtime.connect(goopgExtensionId);

port.onDisconnect.addListener(function() {
    console.log("Failed to connect: " + chrome.runtime.lastError.message);
});

port.onMessage.addListener(function(msg) {
    console.log("Received", msg);
    if (msg.status == null)
        return;
    var div = document.getElementsByClassName("m" + msg.id)[0]
    // for (var i = 0; i < div.children.length; i++)
    //     div.children[i].style.display = "none";
    div.children[0].innerHTML = clean_body(div.children[0].innerHTML)
    div.insertBefore(build_alert(msg), div.firstChild);
    // var body = document.createElement('div')
    // body.className = "raw"
    // body.innerHTML = build_body(escapeHtml(msg.data))
    // div.appendChild(body)
});

function get_orig_message(id) {
    var xmlHttp = null;
    xmlHttp = new XMLHttpRequest();
    var auth = GLOBALS[9];
    url = "https://mail.google.com/mail/u/0/?ui=2&ik=" + auth + "&view=om&th=" + id
    xmlHttp.open("GET", url, false);
    xmlHttp.send(null);
    return xmlHttp.responseText;
}

function check_message(id) {
    info = {}
    info.command = "verify"
    info.id = id
    info.message = get_orig_message(id)
    port.postMessage(info)
}

function look_for_messages() {
    messages = document.getElementsByClassName('ii');
    for (var i = 0; i < messages.length; i++) {
        var id = null;
        var classList = messages[i].classList;
        if (classList.contains(GOOPG_CLASS_CHECKED))
            continue;
        for (var j = 0; j < classList.length; j++) {
            if (classList[j].length > 5 && classList[j][0] == 'm') {
                id = classList[j].substring(1);
                messages[i].classList.add(GOOPG_CLASS_CHECKED)
                break;
            }
        }
        if (id)
            check_message(id)
    }
}

document.body.addEventListener('DOMSubtreeModified', look_for_messages, false);
