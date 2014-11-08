"use strict";

function get_py_port() {
    window.console.log("Connecting to py script ...");
    var py_port = window.chrome.runtime.connectNative("com.leoiannacone.goopg");

    py_port.onMessage.addListener(function (bundle) {
        // workaround for bundle utf-8 coming from py
        window.console.log("Received ", bundle);
        if (web_port !== null)
            web_port.postMessage(bundle);
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
    web_port.onMessage.addListener(function (bundle) {
        window.console.log("Sending", bundle);
        try {
            py_port.postMessage(bundle);
        } catch (err) {
            py_port = get_py_port();
            py_port.postMessage(bundle);
        }
    });
});
