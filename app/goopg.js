chrome.runtime.onMessageExternal.addListener(
    function(request, sender, sendResponse) {
        console.log(request, sender, sendResponse)
    }
);
