"use strict";


function add_javascript_to_head(filename) {
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.src = window.chrome.extension.getURL(filename);
    document.getElementsByTagName("head")[0].appendChild(script);
}

add_javascript_to_head('goopg-web-extension-id.js');
add_javascript_to_head('goopg-web-chrome-port.js');
add_javascript_to_head('goopg-web.js');



// This can be the goopg-web.js if we want to hide js in web page
// and make a pure content-script instead. Just expose the GLOBALS[9]
//
// var info = document.createElement('div');
// info.id = "googp-info";
// info.innerHTML = GLOBALS[9];
// document.getElementsByTagName('body')[0].appendChild(info);
