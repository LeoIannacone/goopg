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

from multiprocessing import Process, Queue

from xdg import BaseDirectory

credentials = None


class GMail():

    def __init__(self, username):
        # Path to the client_secret.json file
        # downloaded from the Developer Console
        current_path = os.path.dirname(os.path.abspath(__file__))
        CLIENT_SECRET_FILE = os.path.join(current_path, 'client_secret.json')

        # Check https://developers.google.com/gmail/api/auth/scopes
        # for all available scopes
        OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.modify'

        # Location of the credentials storage file
        cache_dir = os.path.join('goopg', 'storage')
        cache_dir = BaseDirectory.save_cache_path(cache_dir)
        STORAGE = Storage(os.path.join(cache_dir, username))

        # Start the OAuth flow to retrieve credentials
        flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
        http = httplib2.Http()

        # Try to retrieve credentials from storage
        # or run the flow to generate them
        credentials = STORAGE.get()

        if credentials is None or credentials.invalid:
            # call a subprocess as workaround for stdin/stdout
            # blocked by the main process
            queue = Queue()
            p = Process(target=_login, args=(queue, flow, STORAGE, http))
            p.start()
            p.join()
            credentials = queue.get()

        # Authorize the httplib2.Http object with our credentials
        http = credentials.authorize(http)

        # Build the Gmail service from discovery
        self.gmail_service = build('gmail', 'v1', http=http)
        self.messages = self.gmail_service.users().messages()
        self.drafts = self.gmail_service.users().drafts()

    def get(self, id):
        # this return a message.raw in url safe base64
        message = self.messages.get(userId='me', id=id, format='raw').execute()
        # decode it
        message = base64.urlsafe_b64decode(str(message['raw']))
        return email.message_from_string(message)

    def send(self, id, message, delete_draft=True):
        raw = base64.urlsafe_b64encode(message.as_string())
        body = {'raw': raw}
        self.messages.send(userId='me', body=body).execute()
        if delete_draft:
            response = self.drafts.list(userId='me').execute()
            drafts = response['drafts']
            draft_id = None
            for draft in drafts:
                if draft['message']['id'] == id:
                    #print "deleting draft %s" % draft_id
                    draft_id = draft['id']
                    self.drafts.delete(userId='me', id=draft_id).execute()
                    break


def _login(queue, flow, storage, http):
    queue.put(run(flow, storage, http=http))
