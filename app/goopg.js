"use strict";

var web_ports = [];
var py_port = null;

function web_broadcast(bundle) {
    for (var i = 0; i < web_ports.length; i++) {
        try {
            web_ports[i].postMessage(bundle);
        } catch (err) {}
    }
}

function get_py_port() {
    window.console.log("Connecting to py script ...");
    var py_port = window.chrome.runtime.connectNative("com.leoiannacone.goopg");

    py_port.onMessage.addListener(function (bundle) {
        window.console.log("Received ", bundle);
        web_broadcast(bundle);
    });

    py_port.onDisconnect.addListener(function () {
        var error = window.chrome.runtime.lastError.message;
        window.console.log("Failed to connect: " + error);
        web_broadcast({
            'port_error': error
        });
    });
    return py_port;
}

window.chrome.runtime.onConnectExternal.addListener(function (my_web_port) {
    web_ports.push(my_web_port);
    my_web_port.onMessage.addListener(function (bundle) {
        window.console.log("Sending", bundle);
        try {
            py_port.postMessage(bundle);
        } catch (err) {
            py_port = get_py_port();
            py_port.postMessage(bundle);
        }
    });
    my_web_port.onDisconnect.addListener(function () {
        var index = web_ports.indexOf(my_web_port);
        window.console.log("Web port", index, "disconnecting");
        if (index > -1)
            web_ports.splice(index, 1);
    });
});
