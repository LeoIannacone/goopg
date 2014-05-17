# Copyright (C) 2012 W. Trevor King <wking@tremily.us>
#
# This file is part of pgp-mime.
#
# pgp-mime is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pgp-mime is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# pgp-mime.  If not, see <http://www.gnu.org/licenses/>.

# import copy as _copy
# from email import message_from_bytes as _message_from_bytes
# from email.encoders import encode_7or8bit as _encode_7or8bit
# from email.mime.application import MIMEApplication as _MIMEApplication
# from email.mime.multipart import MIMEMultipart as _MIMEMultipart

from email.generator import Generator
from cStringIO import StringIO


def flatten(msg, to_unicode=False):
    """
    Produce flat text output from an email Message instance.
    """
    assert msg is not None
    fp = StringIO()
    g = Generator(fp, mangle_from_=False)
    g.flatten(msg)
    text = fp.getvalue()
    if to_unicode is True:
        encoding = msg.get_content_charset() or "utf-8"
        text = unicode(text, encoding=encoding)
    return text


# def flatten(message) :
#     """Return raw string representation of message."""
#     try:
#         s = StringIO()
#         g = Generator(s, mangle_from_=False, maxheaderlen=0)

#         g.flatten(message)
#         return s.getvalue()

#     finally:
#         s.close()

# def sign(message, **kwargs):
#     body = _flatten(message)
#     signature = str(_sign_and_encrypt_bytes(data=body, **kwargs), 'us-ascii')
#     sig = _MIMEApplication(
#         _data=signature,
#         _subtype='pgp-signature; name="signature.asc"',
#         _encoder=_encode_7or8bit)
#     sig['Content-Description'] = 'OpenPGP digital signature'
#     sig.set_charset('us-ascii')

#     msg = _MIMEMultipart(
#         'signed', micalg='pgp-sha1', protocol='application/pgp-signature')
#     msg.attach(message)
#     msg.attach(sig)
#     msg['Content-Disposition'] = 'inline'
#     return msg

# def encrypt(message, recipients=None, **kwargs):
#     body = _flatten(message)
#     if recipients is None:
#         recipients = [email for name,email in _email_targets(message)]
#         _LOG.debug('extracted encryption recipients: {}'.format(recipients))
#     encrypted = str(_sign_and_encrypt_bytes(
#             data=body, recipients=recipients, **kwargs), 'us-ascii')
#     enc = _MIMEApplication(
#         _data=encrypted,
#         _subtype='octet-stream; name="encrypted.asc"',
#         _encoder=_encode_7or8bit)
#     enc['Content-Description'] = 'OpenPGP encrypted message'
#     enc.set_charset('us-ascii')
#     control = _MIMEApplication(
#         _data='Version: 1\n',
#         _subtype='pgp-encrypted',
#         _encoder=_encode_7or8bit)
#     control.set_charset('us-ascii')
#     msg = _MIMEMultipart(
#         'encrypted',
#         micalg='pgp-sha1',
#         protocol='application/pgp-encrypted')
#     msg.attach(control)
#     msg.attach(enc)
#     msg['Content-Disposition'] = 'inline'
#     return msg

# def sign_and_encrypt(message, signers=None, recipients=None, **kwargs):
#     _strip_bcc(message=message)
#     body = _flatten(message)
#     if recipients is None:
#         recipients = [email for name,email in _email_targets(message)]
#         _LOG.debug('extracted encryption recipients: {}'.format(recipients))
#     encrypted = str(
#         _sign_and_encrypt_bytes(
#             data=body, signers=signers, recipients=recipients, **kwargs),
#         'us-ascii')
#     enc = _MIMEApplication(
#         _data=encrypted,
#         _subtype='octet-stream; name="encrypted.asc"',
#         _encoder=_encode_7or8bit)
#     enc['Content-Description'] = 'OpenPGP encrypted message'
#     enc.set_charset('us-ascii')
#     control = _MIMEApplication(
#         _data='Version: 1\n',
#         _subtype='pgp-encrypted',
#         _encoder=_encode_7or8bit)
#     control.set_charset('us-ascii')
#     msg = _MIMEMultipart(
#         'encrypted',
#         micalg='pgp-sha1',
#         protocol='application/pgp-encrypted')
#     msg.attach(control)
#     msg.attach(enc)
#     msg['Content-Disposition'] = 'inline'
#     return msg


def _get_encrypted_parts(message):
    ct = message.get_content_type()
    assert ct == 'multipart/encrypted', ct
    params = dict(message.get_params())
    assert params.get('protocol', None) == 'application/pgp-encrypted', params
    assert message.is_multipart(), message
    control = body = None
    for part in message.get_payload():
        if part == message:
            continue
        assert part.is_multipart() is False, part
        ct = part.get_content_type()
        if ct == 'application/pgp-encrypted':
            if control:
                raise ValueError('multiple application/pgp-encrypted parts')
            control = part
        elif ct == 'application/octet-stream':
            if body:
                raise ValueError('multiple application/octet-stream parts')
            body = part
        else:
            raise ValueError('unnecessary {} part'.format(ct))
    if not control:
        raise ValueError('missing application/pgp-encrypted part')
    if not body:
        raise ValueError('missing application/octet-stream part')
    return (control, body)


def get_signed_parts(message):
    ct = message.get_content_type()
    assert ct == 'multipart/signed', ct
    params = dict(message.get_params())
    assert params.get('protocol', None) == 'application/pgp-signature', params
    assert message.is_multipart(), message
    body = signature = None
    for part in message.get_payload():
        if part == message:
            continue
        ct = part.get_content_type()
        if ct == 'application/pgp-signature':
            if signature:
                raise ValueError('multiple application/pgp-signature parts')
            signature = part
        else:
            if body:
                raise ValueError('multiple non-signature parts')
            body = part
    if not body:
        raise ValueError('missing body part')
    if not signature:
        raise ValueError('missing application/pgp-signature part')
    return (body, signature)


# def decrypt(message, **kwargs):
#     control, body = _get_encrypted_parts(message)
#     encrypted = body.get_payload(decode=True)
#     if not isinstance(encrypted, bytes):
#         encrypted = encrypted.encode('us-ascii')
#     decrypted, verified, result = _verify_bytes(encrypted, **kwargs)
#     return _message_from_bytes(decrypted)


# def verify(message, **kwargs):
#     ct = message.get_content_type()
#     if ct == 'multipart/encrypted':
#         control, body = _get_encrypted_parts(message)
#         encrypted = body.get_payload(decode=True)
#         if not isinstance(encrypted, bytes):
#             encrypted = encrypted.encode('us-ascii')
#         decrypted, verified, message = _verify_bytes(encrypted)
#         return (_message_from_bytes(decrypted), verified, message)
#     body, signature = get_signed_parts(message)
#     sig_data = signature.get_payload(decode=True)
#     if not isinstance(sig_data, bytes):
#         sig_data = sig_data.encode('us-ascii')
#     decrypted, verified, result = _verify_bytes(
#         flatten(body), signature=sig_data, **kwargs)
#     return (_copy.deepcopy(body), verified, result)
