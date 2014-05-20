"use strict";
var script = document.createElement("script");
script.type = "text/javascript";
script.src = window.chrome.extension.getURL("goopg-web.js");
document.getElementsByTagName("head")[0].appendChild(script);



// This can be the goopg-web.js if we want to hide js in web page
// and make a pure content-script instead. Just expose the GLOBALS[9]
//
// var info = document.createElement('div');
// info.id = "googp-info";
// info.innerHTML = GLOBALS[9];
// document.getElementsByTagName('body')[0].appendChild(info);
