#!/usr/bin/python

from gnupg import GPG
from json import dumps as toJSON
import email
import gpgmail

gpg = GPG()


def verify(data):
    result = []
    message = email.message_from_string(data)
    if message.get_content_type() == 'multipart/mixed':
        message = message.get_payload()[0]
    if message.get_content_type() == 'multipart/signed':
        for verified, contents in gpgmail.signed_parts(message):
            if verified:
                result = verified.__dict__
                if not 'data' in result or not result['data']:
                    result['data'] = contents.get_payload(decode=True)
                else:
                    # get the real content, strip message Headers
                    msg_tmp = email.message_from_string(result['data'])
                    result['data'] = msg_tmp.get_payload(decode=True)
                break
    else:
        result = gpg.verify(data).__dict__
    del(result['gpg'])
    return toJSON(result, indent=4)


def messageFromSignature(signature):
    message = email.Message()
    message['Content-Type'] = 'application/pgp-signature; name="signature.asc"'
    message['Content-Description'] = 'OpenPGP digital signature'
    message.set_payload(signature)
    return message


if __name__ == '__main__':
    print(verify(open('../nosign.txt', 'rb').read()))
    print(verify(open('../sign.inline.txt', 'rb').read()))
    print(verify(open('../sign.attached.txt', 'rb').read()))
    print(verify(open('../sign.attached2.txt', 'rb').read()))
