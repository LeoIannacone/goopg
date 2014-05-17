
regex_clean_html = /(<([^>]+)>)/gi
regex_get_realmsg = /-----BEGIN PGP SIGNED MESSAGE-----(.|[\r\n])+-----END PGP SIGNATURE-----/m
cleaner_div = document.createElement('div')
messages = document.getElementsByClassName('ii')

for (var i = 0 ; i < messages.length ; i++) {
    msg = messages[i].innerHTML
    msg = msg.replace(regex_clean_html, '')
    cleaner_div.innerHTML = msg
    msg = cleaner_div.textContent
    msg_clear = regex_get_realmsg.exec(msg)
    if (msg_clear) msg = msg_clear[0]
    console.log(msg)
}
