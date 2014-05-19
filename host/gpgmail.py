# -*- mode:python; coding:utf-8; -*- Time-stamp: <gpgmail.py - root>
# copyright (c) konstantin.co.uk. all rights reserved.
# Origin: https://code.google.com/p/python-gnupg/issues/
#         attachmentText?id=4&aid=7243301884964405207&name=
#         gpgmail.py&token=2e585ecf0d148cb330041b1b00d769ff

__all__ = ['filter_parts', 'flatten', 'signed_parts']

import re

from cStringIO import StringIO
from email.generator import Generator
from gnupg import GPG


def _armor(container, message, signature):
    if container.get_param('protocol') == 'application/pgp-signature':
        m = re.match(r'^pgp-(.*)$', container.get_param('micalg'))

        if m:
            TEMPLATE = '-----BEGIN PGP SIGNED MESSAGE-----\n' \
                       'Hash: %s\n\n' \
                       '%s\n%s\n'
            s = StringIO()
            text = re.sub(r'(?m)^(-.*)$', r'- \1', flatten(message))

            s.write(TEMPLATE % (m.group(1).upper(),
                                text,
                                signature.get_payload()))
            return s.getvalue()
    return None


def filter_parts(m, f):
    """Iterate over messages that satisfy predicate."""
    for x in m.walk():
        if f(x):
            yield x


def flatten(message):
    """Return raw string representation of message."""
    try:
        s = StringIO()
        g = Generator(s, mangle_from_=False, maxheaderlen=0)

        g.flatten(message)
        return s.getvalue()
    finally:
        s.close()


def signed_parts(message):
    """Iterate over signed parts of message yielding
    GPG verification status and signed contents."""

    f = lambda m: \
        m.is_multipart() and m.get_content_type() == 'multipart/signed' \
        or not m.is_multipart() and m.get_content_maintype() == 'text'

    gpg = GPG()

    for part in filter_parts(message, f):
        if part.is_multipart():
            try:
                signed_part, signature = part.get_payload()
                s = None
                if signature.get_content_type() == 'application/pgp-signature':
                    s = _armor(part, signed_part, signature)
                    yield gpg.verify(s), signed_part

            except ValueError:
                pass

        else:
            payload = part.get_payload(decode=True)
            gpg_regex = [r'^-+BEGIN PGP SIGNED MESSAGE-+\s+(.*\s+)',
                         r'^-+BEGIN PGP SIGNATURE-+\s+(.*\s+)',
                         r'^-+END PGP SIGNATURE-+\s+(.*\s+)']
            try:
                for reg in gpg_regex:
                    if not re.compile(reg, re.M).search(payload):
                        raise ValueError
                signed_part = re.compile(gpg_regex[0],
                                         re.M).split(payload)[-1]
                signed_part = re.compile(gpg_regex[1],
                                         re.M).split(signed_part)[0]
                yield gpg.verify(payload), signed_part
            except (ValueError, IndexError):
                yield gpg.verify(payload), payload
