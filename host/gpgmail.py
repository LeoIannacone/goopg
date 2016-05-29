import re
import email

from cStringIO import StringIO
from email.generator import Generator
from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from gnupg import GPG
from gnupg import logger as GPGLogger

import logging


class GPGMail(object):

    def __init__(self, gpg=None):
        if gpg:
            self.gpg = gpg
        else:
            self.gpg = GPG(gpgbinary="gpg2", use_agent=True)

        GPGLogger.setLevel(logging.DEBUG)

        self.logger = logging.getLogger('GPGMail')

    def _armor(self, container, message, signature):
        """
        Make the armor signed message
        """
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
                        yield self.gpg.verify(s), True, signature.get_filename()

                except ValueError:
                    pass

            else:
                payload = part.get_payload(decode=True)
                yield self.gpg.verify(payload), False, None

    def verify(self, message):
        """Verify signature of a email message and returns the GPG info"""
        result = {}
        for verified, sign_attached, filename in self._signed_parts(message):
            if verified is not None:
                result = verified.__dict__
                break
        if 'status' in result and result['status'] is None:
            return None
        if 'gpg' in result:
            del(result['gpg'])
        if sign_attached:
            result['filename'] = filename
        return result

    def _get_digest_algo(self, signature):
        """
        Returns a string representation of the digest algo used in signature.

        Raises a TypeError if signature.hash_algo does not exists.

        Acceptable values for signature.hash_algo are:
            MD5       1
            SHA1      2
            RMD160    3
            SHA256    8
            SHA384    9
            SHA512   10
            SHA224   11
        See gnupg/include/cipher.h for more info
        """
        values = {
            1:  "MD5",
            2:  "SHA1",
            3:  "RMD160",
            8:  "SHA256",
            9:  "SHA384",
            10: "SHA512",
            11: "SHA224"
        }
        hash_algo = signature.hash_algo
        try:
            if isinstance(hash_algo, (str, unicode)):
                hash_algo = int(hash_algo)
            return values[hash_algo]
        except:
            raise TypeError("Invalid signature hash_algo {}".format(hash_algo))

    def sign(self, message):
        """Sign a email message and return the new message signed as string"""

        if isinstance(message, (str, unicode)):
            message = email.message_from_string(message)

        # Create the basetxt, which contains the original body message

        # If original message is multipart, take the
        # Content-Type and the Body - ignore other Headers..
        if message.is_multipart():
            content_type = 'Content-Type: {}'.format(message['Content-Type'])
            try:
                body = self._flatten(message).split('\n\n', 1)[1]
            except:
                raise ValueError("Message cannot be split in Headers and Body")
            basetxt = '{}\n\n{}'.format(content_type, body)

        # else get only the body message
        else:
            basetxt = MIMEUTF8QPText(message).as_string()

        # See RFC 3156 (Section 5.) to understand these transformations
        # 1. all the lines must end with <CR><LF>
        basetxt = basetxt.replace('\r\n', '\n')\
                         .replace('\n', '\r\n')
        # 2. remove trailing spaces
        basetxt = re.sub(r' +\r\n', '\r\n', basetxt, flags=re.M)

        # signing
        signature = self.gpg.sign(basetxt, detach=True)
        self.logger.error("signature %s %s" % (basetxt, signature))

        # create the new message as multipart/signed (see RFC 3156)
        micalg = "pgp-{}".format(self._get_digest_algo(signature).lower())
        new_message = MIMEMultipart(_subtype="signed", micalg=micalg,
                                    protocol="application/pgp-signature")

        # copy the headers
        header_to_copy = [
            "Date",
            "Subject",
            "From",
            "To",
            "Bcc",
            "Cc",
            "Reply-To",
            "References",
            "In-Reply-To"
        ]
        for h in header_to_copy:
            if h in message:
                new_message[h] = message[h]

        # attach signed_part and signature and return message as string
        return self._attach_signed_parts(new_message, basetxt, signature)

    def _attach_signed_parts(self, message, signed_part, signature):
        """
        Attach the signed_part and signature to the message (MIMEMultipart)
        and returns the new message as str
        """
        # According with RFC 3156 the signed_part in the message
        # must be equal to the signed one.
        # The best way to do this is "hard" attach the parts
        # using strings.

        if not isinstance(signature, (str, unicode)):
            signature = str(signature)

        # get the body of the MIMEMultipart message,
        # remove last lines which close the boundary
        msg_lines = message.as_string().split('\n')[:-3]

        # get the last opening boundary
        boundary = msg_lines.pop()

        # create the signature as attachment
        sigmsg = Message()
        sigmsg['Content-Type'] = 'application/pgp-signature; ' + \
                                 'name="signature.asc"'
        sigmsg['Content-Description'] = 'GooPG digital signature'
        sigmsg.set_payload(signature)

        # attach the signed_part
        msg_lines += [boundary, signed_part]
        # attach the signature
        msg_lines += [boundary,
                      sigmsg.as_string(),
                      '{}--'.format(boundary)]
        # return message a string
        return '\n'.join(msg_lines)


class MIMEUTF8QPText(MIMENonMultipart):
    """
    This class is used to have a message with:
      Content-Transfer-Encoding: quoted-printable
    As required in RFC 3156
    """
    def __init__(self, message):
        MIMENonMultipart.__init__(self, 'text', 'plain',
                                  charset='utf-8')
        utf8qp = email.charset.Charset('utf-8')
        utf8qp.body_encoding = email.charset.QP
        payload = message.get_payload(decode=True)
        self.set_payload(payload, charset=utf8qp)
