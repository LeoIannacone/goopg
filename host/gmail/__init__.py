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


class GMail():

    def __init__(self, username):
        # the main username
        self.username = username

        # Path to the client_secret.json file
        # downloaded from the Developer Console
        current_path = os.path.dirname(os.path.abspath(__file__))
        CLIENT_SECRET_FILE = os.path.join(current_path, 'client_secret.json')

        # Check https://developers.google.com/gmail/api/auth/scopes
        # for all available scopes
        OAUTH_SCOPE = 'https://mail.google.com/'

        # Location of the credentials storage file
        cache_dir = os.path.join('goopg', 'storage')
        cache_dir = BaseDirectory.save_cache_path(cache_dir)
        STORAGE = Storage(os.path.join(cache_dir, username))

        # Start the OAuth flow to retrieve credentials
        flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
        http = httplib2.Http()

        # Try to retrieve credentials from storage
        # or run the flow to generate them
        self.credentials = STORAGE.get()

        if self.credentials is None or self.credentials.invalid:
            # call a subprocess as workaround for stdin/stdout
            # blocked by the main process
            queue = Queue()
            p = Process(target=_login, args=(queue, flow, STORAGE, http))
            p.start()
            p.join()
            self.credentials = queue.get()

        # Authorize the httplib2.Http object with our credentials
        http = self.credentials.authorize(http)

        # Build the Gmail service from discovery
        self.gmail_service = build('gmail', 'v1', http=http)
        self.messages = self.gmail_service.users().messages()
        self.drafts = self.gmail_service.users().drafts()

        # Use smtp as workaround to send message, GMail API
        # bugged with Content-Type: multipart/signed
        self._smtp_login()

    def _smtp_login(self):
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
        smpt_auth_b64
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



def _login(queue, flow, storage, http):
    queue.put(run(flow, storage, http=http))
