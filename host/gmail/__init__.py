import httplib2
import base64
import email
import os
import sys
import logging

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

from smtplib import SMTP, SMTPServerDisconnected
from multiprocessing import Process, Queue

from xdg import BaseDirectory

from logger import StreamToLogger


# Check https://developers.google.com/gmail/api/auth/scopes
# for all available scopes
OAUTH_SCOPE = 'https://mail.google.com/'

# Path to the client_secret.json, file comes from the Google Developer Console
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'client_secret.json')

# Directory where the credentials storage files are placed
STORAGE_DIR = BaseDirectory.save_cache_path(os.path.join('goopg', 'storage'))


class Gmail():

    def __init__(self, username):
        # the main username
        self.username = username
        self.http = httplib2.Http()
        self.logger = logging.getLogger('Gmail')

        # Start the OAuth flow to retrieve credentials
        flow = flow_from_clientsecrets(CLIENT_SECRET_FILE,
                                       scope=OAUTH_SCOPE)

        # The storage for current user
        storage = Storage(os.path.join(STORAGE_DIR, self.username))

        # Try to retrieve credentials from storage
        # or run the flow to generate them
        self.credentials = storage.get()
        if self.credentials is None or self.credentials.invalid:
            # call a subprocess as workaround for stdin/stdout
            # blocked by the main process, this is the main function:
            def _subprocess_login():
                sys.stdout = StreamToLogger(self.logger, logging.DEBUG)
                sys.stderr = StreamToLogger(self.logger, logging.ERROR)
                queue.put(run(flow, storage, http=self.http))

            # A Queue to get the result from subprocess
            queue = Queue()
            p = Process(target=_subprocess_login)
            self.logger.debug("start login process")
            p.start()
            p.join()
            self.logger.debug("end login process")
            # Retrieve the credentials
            self.credentials = queue.get()

        # Access to the Gmail APIs
        self._gmail_API_login()

        # Use smtp as workaround to send message, GMail API
        # bugged with Content-Type: multipart/signed
        self._smtp_login()

    def _gmail_API_login(self):
        """
        Login in Gmail APIs
        """
        self._refresh_credentials()

        # Authorize the httplib2.Http object with our credentials
        authorized_http = self.credentials.authorize(self.http)

        # Build the Gmail service from discovery
        self.gmail_service = build('gmail', 'v1', http=authorized_http)
        self.messages = self.gmail_service.users().messages()
        self.drafts = self.gmail_service.users().drafts()

    def _refresh_credentials(self):
        """Refresh credentials if needed"""
        if self.credentials.access_token_expired:
            self.logger.info("credentials expired - refreshing")
            self.credentials.refresh(self.http)

    def _smtp_login(self):
        """
        Login in Gmail smtp
        """
        self._refresh_credentials()

        # initialize SMTP procedure
        self.smtp = SMTP('smtp.gmail.com', 587)

        if self.logger.getEffectiveLevel() == logging.DEBUG:
            self.smtp.set_debuglevel(True)
        self.smtp.starttls()
        self.smtp.ehlo()

        # XOATH2 authentication
        smtp_auth_string = 'user={}\1auth=Bearer {}\1\1'
        access_token = self.credentials.access_token
        smtp_auth_string = smtp_auth_string.format(self.username,
                                                   access_token)
        smpt_auth_b64 = base64.b64encode(smtp_auth_string)
        # smtp login
        self.smtp.docmd("AUTH", "XOAUTH2 {}".format(smpt_auth_b64))
        self.smtp.send("\r\n")

    def get(self, id):
        """
        Get a Message from the Gmail message id (as known as X-GM-MSGID).
        """
        self.logger.info('getting message {}'.format(id))
        # this return a message.raw in url safe base64
        message = self.messages.get(userId='me', id=id, format='raw').execute()
        # decode it
        message = base64.urlsafe_b64decode(str(message['raw']))
        self.logger.debug('message id {}\n{}'.format(id, message))
        message = email.message_from_string(message)
        return message

    def get_headers(self, id, headers=None):
        """
        Get the headers of a Gmail message id (as known as X-GM-MSGID).
        If headers (list) is given, only include the headers specified.
        """

        self.logger.info('getting the headers {} of message {}'
                         .format(headers, id))
        message = self.messages.get(userId='me',
                                    id=id,
                                    format='metadata',
                                    metadataHeaders=headers).execute()
        # build a dict for the headers, pythonic way
        result = {}
        for header_msg in message['payload']['headers']:
            result[header_msg['name']] = header_msg['value']

        self.logger.debug('headers of message {}: {}'
                          .format(id, result))
        return result

    def message_matches(self, id, query, rfc822msgid=None):
        """
        Check if the Gmail message id (as known as X-GM-MSGID) matches
        the query.

        Value rfc822msgid is optional (if None will be automatically requested),
        and represents the the value of Message-ID in the header of the message.

        Query is defined as the same str used in the Gmail search box:
        https://support.google.com/mail/answer/7190
        """
        self.logger.info('check if message {} matches query: {}'
                         .format(id, query))

        if rfc822msgid is None:
            headers = self.get_headers(id, ['Message-ID'])
            if ['Message-ID'] in headers:
                rfc822msgid = headers['Message-ID']

        result = False

        if rfc822msgid:
            # build the query adding the Message-ID
            q = "rfc822msgid:{} {}".format(rfc822msgid, query)
            found = self.messages.list(userId='me',
                                       includeSpamTrash=True,
                                       q=q,
                                       fields='messages').execute()
            # look for the same message id in found
            if 'messages' in found:
                for m in found['messages']:
                    if m['id'] == id:
                        result = True
                        break

        self.logger.info('message {} matches the query: {} - [{}]'
                         .format(id, query, result))
        return result

    @staticmethod
    def _get_receivers(message):
        """
        Get the sender and receivers from message (email.Message)
        Receivers are defined into To, Cc and Bcc message header
        """
        receivers = []
        for header in ['To', 'Cc', 'Bcc']:
            if header in message:
                receivers += message.get_all(header, [])

        addresses = []
        for name, addr in email.utils.getaddresses(receivers):
            addresses.append(addr)
        return addresses

    @staticmethod
    def _remove_bcc_from_header(message):
        """
        Return a new message (str) without the Bcc field
        """

        if not isinstance(message, (str, unicode)):
            message = message.as_string()

        # split the message in header and body
        header, body = message.split('\n\n', 1)

        # check for Bcc in headers and remove it
        headers = header.split('\n')
        for i in range(0, len(headers)):
            line = headers[i]
            if line.find('Bcc:') == 0:
                headers.pop(i)
                # check if next lines start with ' ', which means
                # Bcc field is continuing, and remove them
                i += 1
                max_length = len(headers)
                while(i < max_length and headers[i].find(' ') == 0):
                    headers.pop(i)
                break
        header = '\n'.join(headers)

        # return the new message
        return '\n\n'.join([header, body])

    def send(self, id, message, delete_draft=True):

        if isinstance(message, (str, unicode)):
            msg_str = message
            message = email.message_from_string(message)
        else:
            msg_str = message.as_string()

        receivers = self._get_receivers(message)

        if receivers is None or len(receivers) is 0:
            raise ValueError("receiver is None")

        if 'Bcc' in message:
            msg_str = self._remove_bcc_from_header(msg_str)

        # APIs do not work, they reset the multipart/signed Content-type
        # to multipart/mixed
        # raw = base64.urlsafe_b64encode(msg_str)
        # self.messages.send(userId='me', body={'raw': raw}).execute()

        try:
            self.smtp.sendmail(self.username, receivers, msg_str)
        except SMTPServerDisconnected:
            self.logger.info('smtp disconnected - reconnecting')
            self._smtp_login()
            self.smtp.sendmail(self.username, receivers, msg_str)
