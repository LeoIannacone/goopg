GOOPG_CLASS_PREFIX = "goopg-"
GOOPG_CLASS_CHECKED = GOOPG_CLASS_PREFIX + "checked"

function get_orig_message(id) {
    var xmlHttp = null;
    xmlHttp = new XMLHttpRequest();
    var auth = GLOBALS[9];
    console.log(auth)
    url = "https://mail.google.com/mail/u/0/?ui=2&ik=" + auth + "&view=om&th=" + id
    xmlHttp.open("GET", url, false);
    xmlHttp.send(null);
    return xmlHttp.responseText;
}

function check_message(id) {
    info = {}
    info.id = id
    info.message = get_orig_message(id)
    chrome.runtime.sendMessage('ddlebbablilfigfkkjedbpapjichmjgd', info,
        function(response) {
            console.log("Received " + response);
        });
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

// var divs = document.getElementsByTagName('div')
// for (var i = 0; i < divs.length; i++) {
//     if (divs[i].getAttribute('role') == 'main') {
//         divs[i].addEventListener('DOMSubtreeModified', look_for_messages, false);
//         break;
//     }
// }

document.body.addEventListener('DOMSubtreeModified', look_for_messages, false);
