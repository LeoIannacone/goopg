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
        # check the message only if message['force']
        check = message['force'] if 'force' in message else False
        # or content_type of message contains 'multipart/signed'
        if not check:
            content_type = self.gmail.get_header(id, 'Content-Type')
            check = content_type.find('multipart/signed') >= 0

        if check:
            mail = self.gmail.get(id)
            return self.gpgmail.verify(mail)
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
