# See https://developers.google.com/gmail/api/quickstart/quickstart-python?hl=it

#!/usr/bin/python

import httplib2
import base64
import email
import os

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

from smtplib import SMTP, SMTPServerDisconnected
from multiprocessing import Process, Queue

from xdg import BaseDirectory


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
        # this return a message.raw in url safe base64
        message = self.messages.get(userId='me', id=id, format='raw').execute()
        # decode it
        message = base64.urlsafe_b64decode(str(message['raw']))
        return email.message_from_string(message)

    def send(self, id, message, delete_draft=True):
        # APIs do not work
        # raw = base64.urlsafe_b64encode(message.as_string())
        # body = {'raw': raw}
        # self.messages.send(userId='me', body=body).execute()
        # if delete_draft:
        #     response = self.drafts.list(userId='me').execute()
        #     drafts = response['drafts']
        #     draft_id = None
        #     for draft in drafts:
        #         if draft['message']['id'] == id:
        #             #print "deleting draft %s" % draft_id
        #             draft_id = draft['id']
        #             self.drafts.delete(userId='me', id=draft_id).execute()
        #             break
        sender = message['From']
        receiver = message['To']
        try:
            self.smtp.sendmail(sender, receiver, message.as_string())
        except SMTPServerDisconnected:
            self._smtp_login()
            self.smtp.sendmail(sender, receiver, message.as_string())
