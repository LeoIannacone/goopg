#!/usr/bin/python

import email
import gpgmail


def _get_decoded_payload(message):
    if message.get_content_charset():
        result = message.get_payload(decode=True)
        result = result.decode(message.get_content_charset())
        return result
    else:
        return message.get_payload()


def verify(data):
    result = {}
    message = email.message_from_string(data)
    for verified, contents in gpgmail.signed_parts(message):
        if verified is not None:
            result = verified.__dict__
            break
    if 'gpg' in result:
        del(result['gpg'])
    return result


def messageFromSignature(signature):
    message = email.Message()
    message['Content-Type'] = 'application/pgp-signature; name="signature.asc"'
    message['Content-Description'] = 'OpenPGP digital signature'
    message.set_payload(signature)
    return message


if __name__ == '__main__':
    import json

    def pJSON(d):
        print json.dumps(d, indent=4)

    pJSON(verify(open('../nosign.txt', 'rb').read()))
    pJSON(verify(open('../sign.inline.txt', 'rb').read()))
    pJSON(verify(open('../sign.attached.txt', 'rb').read()))
    pJSON(verify(open('../sign.attached2.txt', 'rb').read()))
    pJSON(verify(open('/tmp/clean', 'rb').read()))
