from gpgmail import GPGMail
from gmail import GMail

import logging


class CommandHandler(object):

    def __init__(self):
        self.gmail = None
        self.gpgmail = None
        self.initialized = False
        self.logger = logging.getLogger('CommandHandler')

    def parse(self, message):
        result = None
        command = message["command"]
        if command == 'init':
            result = self.init(message)
        elif command == 'verify':
            result = self.verify(message)
        elif command == 'sign':
            result = self.sign(message)
        return result

    def init(self, message):
        if not 'options' in message and not 'username' in message['options']:
            return False
        self.gpgmail = GPGMail()
        self.gmail = GMail(message['options']['username'])
        self.initialized = True
        return True

    def verify(self, message):
        if not self.initialized:
            return False

        id = message['id']

        def _verify():
            mail = self.gmail.get(id)
            return self.gpgmail.verify(mail)

        # verify the message only if message['force'] = true
        if 'force' in message and message['force']:
            return _verify()

        # or content_type of message is 'multipart/signed'
        headers = self.gmail.get_headers(id, ['Content-Type', 'Message-ID'])
        if 'Content-Type' in headers:
            content_type = headers['Content-Type']
            if content_type.find('multipart/signed') >= 0:
                return _verify()

            # or if message is multipart and it may contain a pgp-signature
            is_multipart = content_type.find('multipart/') >= 0
            if (is_multipart and 'Message-ID' in headers):
                rfc822msgid = headers['Message-ID']
                query = '("BEGIN PGP SIGNATURE" "END PGP SIGNATURE")'
                match = self.gmail.message_matches(id, query, rfc822msgid)
                if match:
                    return _verify()
        # else
        return None

    def sign(self, message):
        if not self.initialized or not message["id"]:
            return False
        result = False
        try:
            draft = self.gmail.get(message["id"])
            new_message = self.gpgmail.sign(draft)
            if new_message:
                self.gmail.send(message["id"], new_message)
                result = True
        except Exception, e:
            self.logger.exception(e)
        finally:
            return result
