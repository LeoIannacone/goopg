/* global GOOPG_EXTENSION_ID */

"use strict";

// port to communicate with background
var web_port = null;

var Port = {
    // return a new port
    get: function () {
        window.console.log("Connecting to web port...");

        var port = window.chrome.runtime.connect(GOOPG_EXTENSION_ID);

        port.onDisconnect.addListener(function () {
            window.console.log("Failed to connect: " + window.chrome.runtime.lastError.message);
        });

        port.onMessage.addListener(Port.handler);

        return port;
    },

    // send a bundle
    send: function (bundle) {
        try {
            web_port.postMessage(bundle);
        } catch (err) {
            web_port = Port.get();
            web_port.postMessage(bundle);
        }
    },

    handler: function (bundle) {
        // This must is implemented elsewhere
        return;
    }

};
