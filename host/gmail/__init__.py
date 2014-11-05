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

from util import StreamToLogger


# Check https://developers.google.com/gmail/api/auth/scopes
# for all available scopes
OAUTH_SCOPE = 'https://mail.google.com/'

# Path to the client_secret.json, file comes from the Google Developer Console
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'client_secret.json')

# Directory where the credentials storage files are placed
STORAGE_DIR = BaseDirectory.save_cache_path(os.path.join('goopg', 'storage'))


class GMail():

    def __init__(self, username):
        # the main username
        self.username = username
        self.http = httplib2.Http()

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
                logger = logging.getLogger('GMailLogin')
                sys.stdout = StreamToLogger(logger, logging.INFO)
                sys.stderr = StreamToLogger(logger, logging.ERROR)
                queue.put(run(flow, storage, http=self.http))

            # A Queue to get the result from subprocess
            queue = Queue()
            p = Process(target=_subprocess_login)
            p.start()
            p.join()
            # Retreive the credentials
            self.credentials = queue.get()

        # Access to the GMail APIs
        self._gmail_API_login()

        # Use smtp as workaround to send message, GMail API
        # bugged with Content-Type: multipart/signed
        self._smtp_login()

    def _gmail_API_login(self):
        """
        Login in GMail APIs
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
            self.credentials.refresh(self.http)

    def _smtp_login(self):
        """
        Loging in GMail smtp
        """
        self._refresh_credentials()

        # intialize SMTP procedure
        self.smtp = SMTP('smtp.gmail.com', 587)

        #self.smtp.set_debuglevel(True)
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
        Get a Message from the GMail message id (as known as X-GM-MSGID)
        """
        # this return a message.raw in url safe base64
        message = self.messages.get(userId='me', id=id, format='raw').execute()
        # decode it
        message = base64.urlsafe_b64decode(str(message['raw']))
        return email.message_from_string(message)

    def get_header(self, id, header):
        """
        Get the specified header of a GMail message id (as known as X-GM-MSGID).
        Returns None if header not found.
        """
        message = self.messages.get(userId='me',
                                    id=id,
                                    format='metadata',
                                    metadataHeaders=header).execute()

        try:
            for header_msg in message['payload']['headers']:
                if header_msg['name'] == header:
                    return header_msg['value']
        except:
            return None

    @staticmethod
    def _get_sender_and_receivers(message):
        """
        Get the sender and receivers from messaage (email.Message)
        Receivers are defined into To, Cc and Bcc message header
        """
        receivers = []
        for header in ['To', 'Cc', 'Bcc']:
            if header in message:
                receivers.append(message[header])

        sender = message['From']
        receivers = ','.join(receivers).split(',')
        # strip receives
        receivers = [r.strip() for r in receivers]

        return sender, receivers

    @staticmethod
    def _remove_bcc_from_header(message):
        """
        Return a new message (str) without the Bcc field
        """

        if not isinstance(message, (str, unicode)):
            message = message.as_string()

        # slipt the message in header and body
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
        # APIs do not work
        # raw = base64.urlsafe_b64encode(message.as_string())
        # body = {'raw': raw}
        # self.messages.send(userId='me', body=body).execute()

        if isinstance(message, (str, unicode)):
            msg_str = message
            message = email.message_from_string(message)
        else:
            msg_str = message.as_string()

        sender, receivers = self._get_sender_and_receivers(message)

        if sender is None:
            raise ValueError("sender is None")
        if receivers is None:
            raise ValueError("receiver is None")

        if 'Bcc' in message:
            msg_str = self._remove_bcc_from_header(msg_str)

        try:
            self.smtp.sendmail(sender, receivers, msg_str)
        except SMTPServerDisconnected:
            self._smtp_login()
            self.smtp.sendmail(sender, receivers, msg_str)
