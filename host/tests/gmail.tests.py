import unittest
import sys
import os

from email.message import Message

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
        m = Message()
        my_sender = 'Me <me@tests.com>'
        to = 'Leo Iannacone <leo@tests.com>'
        Cc = 'Leo2 Iannacone <leo2@tests.com>, Leo3 Iannacone <leo3@tests.com>'
        Bcc = 'Leo4 Iannacone <leo4@tests.com>, Leo5 Iannacone <leo5@tests.com>'
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


if __name__ == '__main__':
    unittest.main()
