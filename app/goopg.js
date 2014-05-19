function utf8_to_b64(str) {
    return window.btoa(encodeURIComponent(escape(str)));
}

function b64_to_utf8(str) {
    return unescape(decodeURIComponent(window.atob(str)));
}

function python_utf8_wa(json) {
    try {
        var data = "" + json['data']
        delete json.data
        json = JSON.parse(decodeURIComponent(escape(JSON.stringify(json))))
        json['data'] = data
        return json
    } catch (err) {
        return json
    }
}

function get_py_port() {
    console.log("Connecting to py script ...")
    var py_port = chrome.runtime.connectNative("com.leoiannacone.goopg");

    py_port.onMessage.addListener(function (msg) {
        // workaround for msg utf-8 coming from py
        msg = python_utf8_wa(msg)
        console.log("Received ", msg);
        if (web_port != null)
            web_port.postMessage(msg)
        else
            console.log("web port is null")
    });

    py_port.onDisconnect.addListener(function () {
        console.log("Failed to connect: " + chrome.runtime.lastError.message);
    });

    return py_port;
}

var web_port = null;
var py_port = null;

chrome.runtime.onConnectExternal.addListener(function (my_web_port) {
    web_port = my_web_port;
    web_port.onMessage.addListener(function (request) {
        full_message = "X-GM-MSGID: " + request.id + "\n"
        full_message += request.message
        hash = utf8_to_b64(full_message)
        console.log("Recevided request for", request.id, "data length", hash.length)
        try {
            py_port.postMessage(hash)
        } catch (err) {
            py_port = get_py_port();
            py_port.postMessage(hash);
        }
    });
});
