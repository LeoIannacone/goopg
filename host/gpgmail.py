# -*- mode:python; coding:utf-8; -*- Time-stamp: <gpgmail.py - root>
# copyright (c) konstantin.co.uk. all rights reserved.
# Origin: https://code.google.com/p/python-gnupg/issues/
#         attachmentText?id=4&aid=7243301884964405207&name=
#         gpgmail.py&token=2e585ecf0d148cb330041b1b00d769ff

#__all__ = ['_filter_parts', '_flatten', '_signed_parts']

import re

from cStringIO import StringIO
from email.generator import Generator
from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email
from gnupg import GPG


class GPGMail(object):

    def __init__(self):
        self.gpg = GPG(use_agent=True)

    def _armor(self, container, message, signature):
        if container.get_param('protocol') == 'application/pgp-signature':
            m = re.match(r'^pgp-(.*)$', container.get_param('micalg'))

            if m:
                TEMPLATE = '-----BEGIN PGP SIGNED MESSAGE-----\n' \
                           'Hash: %s\n\n' \
                           '%s\n%s\n'
                s = StringIO()
                text = re.sub(r'(?m)^(-.*)$', r'- \1', self._flatten(message))

                s.write(TEMPLATE % (m.group(1).upper(),
                                    text,
                                    signature.get_payload()))
                return s.getvalue()
        return None

    def _filter_parts(sefl, m, f):
        """Iterate over messages that satisfy predicate."""
        for x in m.walk():
            if f(x):
                yield x

    def _flatten(self, message):
        """Return raw string representation of message."""
        try:
            s = StringIO()
            g = Generator(s, mangle_from_=False, maxheaderlen=0)

            g.flatten(message)
            return s.getvalue()
        finally:
            s.close()

    def _signed_parts(self, message):
        """Iterate over signed parts of message yielding
        GPG verification status and signed contents."""

        f = lambda m: \
            m.is_multipart() and m.get_content_type() == 'multipart/signed' \
            or not m.is_multipart() and m.get_content_maintype() == 'text'

        for part in self._filter_parts(message, f):
            if part.is_multipart():
                try:
                    signed_part, signature = part.get_payload()
                    s = None
                    sign_type = signature.get_content_type()
                    if sign_type == 'application/pgp-signature':
                        s = self._armor(part, signed_part, signature)
                        yield self.gpg.verify(s), signature.get_filename()

                except ValueError:
                    pass

            else:
                payload = part.get_payload(decode=True)
                yield self.gpg.verify(payload), None

    def _messageFromSignature(self, signature):
        message = Message()
        message['Content-Type'] = 'application/pgp-signature; ' + \
                                  'name="signature.asc"'
        message['Content-Description'] = 'GooPG digital signature'
        message.set_payload(signature)
        return message

    def verify(self, message):
        result = {}
        for verified, filename in self._signed_parts(message):
            if verified is not None:
                result = verified.__dict__
                break
        if 'status' in result and result['status'] is None:
            return None
        if 'gpg' in result:
            del(result['gpg'])
        result['filename'] = filename
        return result

    def sign(self, message):
        new_message = MIMEMultipart(_subtype="signed", micalg="pgp-sha512",
                                    protocol="application/pgp-signature")
        for i in ["Date", "To", "From", "Subject", "Bcc", "Cc"]:
            if i in message:
                new_message[i] = message[i]

        for part in message.walk():
            if part.get_content_maintype() == 'text':
                body = part.get_payload()
                basemsg = MIMEUTF8QPText(body)
                basetxt = basemsg.as_string().replace('\n', '\r\n')
                signature = str(self.gpg.sign(basetxt, detach=True))
                new_message.attach(basemsg)
                new_message.attach(self._messageFromSignature(signature))

                # # start sign inline
                # new_message = Message()
                # signature = str(self.gpg.sign(body))
                # new_message.set_payload(signature)
                # # end sign inline
            elif part.get_content_maintype() == 'application':
                new_message.attach(part)
        return new_message


class MIMEUTF8QPText(email.mime.nonmultipart.MIMENonMultipart):
    def __init__(self, payload):
        email.mime.nonmultipart.MIMENonMultipart.__init__(self, 'text', 'plain',
                                                          charset='utf-8')
        utf8qp = email.charset.Charset('utf-8')
        utf8qp.body_encoding = email.charset.QP
        self.set_payload(payload, charset=utf8qp)
