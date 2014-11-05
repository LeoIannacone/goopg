import unittest
import sys
import os
import email

from email.message import Message
from email.mime.text import MIMEText

# change the syspath to import Gmail
# FIX_ME: make module name
current = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(current)

from gmail import GMail


class gmail_tests(unittest.TestCase):
    def test_sends_to_everyone(self):
        """
        Tests if message is going to be sent to:
          To:
          CC:
          Bcc:
        """
        my_sender = 'Me <me@tests.com>'
        to = 'Leo Iannacone <leo@tests.com>'
        Cc = 'Leo2 Iannacone <leo2@tests.com>, Leo3 Iannacone <leo3@tests.com>'
        Bcc = 'Leo4 Iannacone <leo4@tests.com>, Leo5 Iannacone <leo5@tests.com>'
        m = Message()
        m['To'] = to
        m['Cc'] = Cc
        m['Bcc'] = Bcc
        m['From'] = my_sender

        my_receivers = ', '.join([to, Cc, Bcc]).split(',')
        # strip receives
        my_receivers = [r.strip() for r in my_receivers]
        sender, receivers = GMail._get_sender_and_receivers(m)

        self.assertEqual(sender, my_sender)
        self.assertEqual(receivers, my_receivers)

    def test_remove_bcc_from_header(self):
        """
        Test if Bcc is removed from message header before send it
        """
        my_sender = 'Me <me@tests.com>'
        to = 'Leo Iannacone <leo@tests.com>'
        Cc = 'Leo2 Iannacone <leo2@tests.com>, Leo3 Iannacone <leo3@tests.com>'
        Bcc = ['Leo{0} Nnc <leo{0}@tests.com>'.format(i) for i in range(4, 30)]
        Bcc = ', '.join(Bcc)
        payload = 'This is the payload of test_remove_bcc_from_header'
        m = MIMEText(payload)
        m['To'] = to
        m['Cc'] = Cc
        m['Bcc'] = Bcc
        m['From'] = my_sender

        new_message = GMail._remove_bcc_from_header(m)

        # message must be a correct email (parsable)
        new_message = email.message_from_string(new_message)
        self.assertIsInstance(new_message, Message)

        # must not have 'Bcc'
        self.assertFalse('Bcc' in new_message)

        # and must have the same payload
        self.assertEqual(payload, new_message.get_payload())


if __name__ == '__main__':
    unittest.main()
