function utf8_to_b64(str) {
    return window.btoa(encodeURIComponent(escape(str)));
}

function b64_to_utf8(str) {
    return unescape(decodeURIComponent(window.atob(str)));
}

function python_utf8_wa(json) {
    return JSON.parse(decodeURIComponent(escape(JSON.stringify(json))))
}

var lastSendResponse;

function sendResponseToWeb(response) {
    console.log("Sending to web", response)
    lastSendResponse(response);
}

var web_port = null;
var py_port = chrome.runtime.connectNative("com.leoiannacone.goopg");

py_port.onMessage.addListener(function(msg) {
    // workaround for msg utf-8 coming from py
    msg = python_utf8_wa(msg)
    console.log("Received ", msg);
    if (web_port != null)
        web_port.postMessage(msg)
    else
        console.log("web port is null")
});

py_port.onDisconnect.addListener(function() {
    console.log("Failed to connect: " + chrome.runtime.lastError.message);
});

chrome.runtime.onConnectExternal.addListener(function(my_web_port) {
    web_port = my_web_port;
    web_port.onMessage.addListener(function(request) {
        full_message = "X-GM-MSGID: " + request.id + "\n"
        full_message += request.message
        hash = utf8_to_b64(full_message)
        console.log("Recevided request for", request.id, "data length", hash.length)
        py_port.postMessage(hash)
    });
});
