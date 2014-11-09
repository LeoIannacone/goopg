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
        self.logger = logging.getLogger('GMail')

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

        # Access to the GMail APIs
        self._gmail_API_login()

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
            self.logger.info("credentials expired - refreshing")
            self.credentials.refresh(self.http)

    def get(self, id):
        """
        Get a Message from the GMail message id (as known as X-GM-MSGID).

        Returns the message (Message) and the threadId (as known as X-GM-THRID)
        it belongs to.
        """
        self.logger.info('getting message {}'.format(id))
        # this return the message with a raw field in url safe base64
        gm_message = self.messages.get(userId='me',
                                       id=id,
                                       format='raw').execute()
        # decode it
        message = base64.urlsafe_b64decode(str(gm_message['raw']))
        # get the threadId it belongs to
        threadId = gm_message['threadId']

        self.logger.debug('message id {}\n{}'.format(id, message))

        message = email.message_from_string(message)
        return message, threadId

    def get_headers(self, id, headers=None):
        """
        Get the headers of a GMail message id (as known as X-GM-MSGID).
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
        Check if the GMail message id (as known as X-GM-MSGID) matches
        the query.

        Value rfc822msgid is optional (if None will be automatically requested),
        and represents the the value of Message-ID in the header of the message.

        Query is defined as the same str used in the GMail search box:
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

    def send(self, message, threadId=None):
        """
        Send a message (str or Message).

        If message is In-Reply-To, the threadId (as known as X-GM-THRID)
        must be passed. It can be get via the get() function.
        """

        if not isinstance(message, (str, unicode)):
            message = message.as_string()

        body = {'raw': base64.urlsafe_b64encode(message)}

        if threadId is not None:
            body['threadId'] = threadId

        self.messages.send(userId='me', body=body).execute()
