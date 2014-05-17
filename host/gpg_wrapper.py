#!/usr/bin/python

from gnupg import GPG
from json import dumps as toJSON
import email
import gpgmail

gpg = GPG()


def verify(data):
    message = email.message_from_string(data)
    if message.get_content_type() == 'multipart/mixed':
        message = message.get_payload()[0]
    if message.get_content_type() == 'multipart/signed':
        for verified, contents in gpgmail.signed_parts(message):
            if verified:
                break
    else:
        verified = gpg.verify(data)
    verified = verified.__dict__
    del(verified['gpg'])
    return toJSON(verified, indent=4)


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
    print(verify(open('/home/l3on/tmp/0.txt', 'rb').read()))
