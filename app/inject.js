var script = document.createElement('script');
script.type = 'text/javascript';
script.src = chrome.extension.getURL('goopg-web.js');
document.getElementsByTagName('head')[0].appendChild(script);
