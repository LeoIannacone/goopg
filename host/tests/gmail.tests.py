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
    pass

if __name__ == '__main__':
    unittest.main()
