#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import sys
import os
import email

from email.mime.text import MIMEText

# change the syspath to import GPGMail
# FIX_ME: make module name
current = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current, '..'))

from gpgmail import GPGMail


class BaseTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        #super(unittest.TestCase, self).__init__(*args, **kwargs)
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.gpgmail = GPGMail()

    def _verify_file(self, filename):
        filename = os.path.join(current, 'emails', filename)
        with open(filename, 'r') as fd:
            message = email.message_from_file(fd)
            return self.gpgmail.verify(message)

    def _sign_file(self, filename):
        filename = os.path.join(current, 'emails', filename)
        with open(filename, 'r') as fd:
            message = email.message_from_file(fd)
            return self.gpgmail.sign(message)

    def _assert_rfc3156(self, v):
        self.assertIsNotNone(v)
        self.assertIn('filename', v)
        self.assertEqual(v['filename'], 'signature.asc')


class Verify(BaseTest):

    def __init__(self, *args, **kwargs):
        #super(BaseTest, self).__init__(*args, **kwargs)
        BaseTest.__init__(self, *args, **kwargs)

    def test_verify_inline_text(self):
        v = self._verify_file('signed.inline')
        self.assertIsNotNone(v)
        self.assertNotIn('filename', v)

    def test_verify_rfc3156_text_plain(self):
        v = self._verify_file('signed.attached.text.plain')
        self._assert_rfc3156(v)

    def test_verify_rfc3156_text_html(self):
        v = self._verify_file('signed.attached.text.html')
        self._assert_rfc3156(v)

    def test_verify_rfc3156_text_plain_with_attachment(self):
        v = self._verify_file('signed.attached.text.plain.with-attachment')
        self._assert_rfc3156(v)

    def test_verify_message_nosigned(self):
        v = self._verify_file('text.plain')
        self.assertIsNone(v)


class Sign(BaseTest):

    def __init__(self, *args, **kwargs):
        #super(BaseTest, self).__init__(*args, **kwargs)
        BaseTest.__init__(self, *args, **kwargs)

    def _verify_message_str(self, message):
        message = email.message_from_string(message)
        v = self.gpgmail.verify(message)
        self._assert_rfc3156(v)

    def test_sign_text_plain(self):
        s = self._sign_file('text.plain')
        self._verify_message_str(s)

    def test_sign_text_html(self):
        s = self._sign_file('text.html')
        self._verify_message_str(s)

    def test_sign_text_plain_with_attachment(self):
        s = self._sign_file('text.plain.with-attachment')
        self._verify_message_str(s)

    def test_same_headers_and_payload(self):
        payload = 'A simple text message with UTF-8 chars\r\nàèéìòù'
        orig_message = MIMEText(payload)
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
            orig_message[h] = '{} of the message'.format(h)

        signed_message_str = self.gpgmail.sign(orig_message)
        signed_message = email.message_from_string(signed_message_str)

        for h in header_to_copy:
            self.assertEqual(orig_message[h], signed_message[h])

        signed_part, signature = signed_message.get_payload()
        self.assertEqual(payload, signed_part.get_payload(decode=True))

if __name__ == '__main__':
    unittest.main()
