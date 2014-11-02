import re
import email

from cStringIO import StringIO
from email.generator import Generator
from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
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

    def verify(self, message):
        """Verify signature of a email message and returns the GPG info"""
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
        """Sign a email message and return the new message signed"""
        # Create the basemsg, which contain the original message
        # If original message has attachments, attach everything..
        if message.get_content_type() == 'multipart/mixed':
            basemsg = MIMEMultipart(_subtype='mixed')
            for part in message.walk():
                # the body message
                if part.get_content_maintype() == 'text':
                    basemsg.attach(MIMEUTF8QPText(part))
                # the attachments
                elif part.get('Content-Disposition'):
                    basemsg.attach(part)
        # else get only the body message
        else:
            basemsg = MIMEUTF8QPText(message)

        # sign the original message
        basetxt = basemsg.as_string()\
                         .replace('\r\n', '\n')\
                         .replace('\n', '\r\n')
        signature = self.gpg.sign(basetxt, detach=True)

        # create the signature message
        sigmsg = Message()
        sigmsg['Content-Type'] = 'application/pgp-signature; ' + \
                                 'name="signature.asc"'
        sigmsg['Content-Description'] = 'GooPG digital signature'
        sigmsg.set_payload(str(signature))

        # create the new message
        micalg = "pgp-{}".format(self._get_digest_algo(signature).lower())
        new_message = MIMEMultipart(_subtype="signed", micalg=micalg,
                                    protocol="application/pgp-signature")
        header_to_copy = [
            "Date",
            "Subject",
            "From",
            "To",
            "Bcc",
            "Cc",
            "Reply-To",
            "Sender",
            "References",
            "In-Reply-To"
        ]
        for h in header_to_copy:
            if h in message:
                new_message[h] = message[h]

        # attach the orig message
        new_message.attach(basemsg)
        # attach the signature
        new_message.attach(sigmsg)

        return new_message


# This class is used to have a message with:
#  Content-Transfer-Encoding: quoted-printable
# It's required in RFC 3156
class MIMEUTF8QPText(MIMENonMultipart):
    def __init__(self, message):
        MIMENonMultipart.__init__(self, 'text', 'plain',
                                  charset='utf-8')
        utf8qp = email.charset.Charset('utf-8')
        utf8qp.body_encoding = email.charset.QP
        payload = message.get_payload(decode=True)
        self.set_payload(payload, charset=utf8qp)
