from gpgmail import GPGMail
from gmail import GMail


class CommandHandler(object):

    def __init__(self):
        self.gmail = None
        self.gpgmail = None
        self.initialized = False

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
        mail = self.gmail.get(message["id"])
        return self.gpgmail.verify(mail)

    def sign(self, message):
        if not self.initialized:
            return False
        draft = self.gmail.get(message["id"])
        new_message = self.gpgmail.sign(draft)
        if new_message:
            self.gmail.send(message["id"], new_message)
            return True
        return False
