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


class GMail():

    def __init__(self):
        # Path to the client_secret.json file
        # downloaded from the Developer Console
        current_path = os.path.dirname(os.path.abspath(__file__))
        CLIENT_SECRET_FILE = os.path.join(current_path, 'client_secret.json')

        # Check https://developers.google.com/gmail/api/auth/scopes
        # for all available scopes
        OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.modify'

        # Location of the credentials storage file
        STORAGE = Storage(os.path.join(current_path, 'gmail.storage'))

        # Start the OAuth flow to retrieve credentials
        flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
        http = httplib2.Http()

        # Try to retrieve credentials from storage
        # or run the flow to generate them
        credentials = STORAGE.get()
        if credentials is None or credentials.invalid:
            credentials = run(flow, STORAGE, http=http)

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

    def send(self, id, message, delete_draft=False):
        raw = base64.urlsafe_b64encode(message.as_string())
        body = {'message': {'raw': raw}}
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


if __name__ == '__main__':
    #print GMail().get('14955b365fa08f14')
    print GMail().send('1495bb566c157b3b', 'm')

