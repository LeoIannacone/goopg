"use strict";

function utf8_to_b64(str) {
    return window.btoa(encodeURIComponent(window.escape(str)));
}

function b64_to_utf8(str) {
    return window.unescape(window.decodeURIComponent(window.atob(str)));
}

function python_utf8_wa(json) {
    try {
        var data = "" + json.data;
        delete json.data;
        json = JSON.parse(decodeURIComponent(window.escape(JSON.stringify(json))));
        json.data = data;
        return json;
    } catch (err) {
        return json;
    }
}

function get_py_port() {
    window.console.log("Connecting to py script ...");
    var py_port = window.chrome.runtime.connectNative("com.leoiannacone.goopg");

    py_port.onMessage.addListener(function (msg) {
        // workaround for msg utf-8 coming from py
        msg = python_utf8_wa(msg);
        window.console.log("Received ", msg);
        if (web_port !== null)
            web_port.postMessage(msg);
        else
            window.console.log("web port is null");
    });

    py_port.onDisconnect.addListener(function () {
        window.console.log("Failed to connect: " + window.chrome.runtime.lastError.message);
    });

    return py_port;
}

var web_port = null;
var py_port = null;

window.chrome.runtime.onConnectExternal.addListener(function (my_web_port) {
    web_port = my_web_port;
    web_port.onMessage.addListener(function (request) {
        var full_message = "X-GM-MSGID: " + request.id + "\n";
        full_message += request.message;
        var hash = utf8_to_b64(full_message);
        window.console.log("Recevided request for", request.id, "data length", hash.length);
        try {
            py_port.postMessage(hash);
        } catch (err) {
            py_port = get_py_port();
            py_port.postMessage(hash);
        }
    });
});
