function utf8_to_b64(str) {
    return window.btoa(encodeURIComponent(escape(str)));
}

function b64_to_utf8(str) {
    return unescape(decodeURIComponent(window.atob(str)));
}

var port = chrome.runtime.connectNative("com.leoiannacone.goopg");
port.onMessage.addListener(function(msg) {
    console.log("Received ", msg);
    if (msg['debug'])
        console.log(msg['debug'])
});

port.onDisconnect.addListener(function() {
    console.log("Failed to connect: " + chrome.runtime.lastError.message);
});

chrome.runtime.onMessageExternal.addListener(
    function(request, sender, sendResponse) {
        hash = utf8_to_b64(request.message)
        console.log("Recevided request for", request.id, "data length", hash.length)
        port.postMessage(hash)
    }
);
