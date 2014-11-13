from gnupg import GPG
from gpgmail import GPGMail
from gmail import Gmail

import logging


class CommandHandler(object):

    def __init__(self):
        self.gpg = None
        self.gmail = None
        self.gpgmail = None
        self.initialized = False
        self.logger = logging.getLogger('CommandHandler')

    def parse(self, bundle):
        result = None
        command = bundle["command"]
        if command == 'init':
            result = self.init(bundle)
        elif command == 'verify':
            result = self.verify(bundle)
        elif command == 'sign':
            result = self.sign(bundle)
        return result

    def init(self, bundle):
        if not 'options' in bundle and not 'username' in bundle['options']:
            return False
        self.gpg = GPG(use_agent=True)
        self.gpgmail = GPGMail(self.gpg)
        self.gmail = Gmail(bundle['options']['username'])
        self.initialized = True
        return True

    def verify(self, bundle):
        if not self.initialized:
            return False

        id = bundle['id']

        def _verify():
            mail = self.gmail.get(id)
            return self.gpgmail.verify(mail)

        # verify the message only if bundle['force'] = true
        if 'force' in bundle and bundle['force']:
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

    def sign(self, bundle):
        if not self.initialized or not bundle["id"]:
            return False
        result = False
        try:
            draft = self.gmail.get(bundle["id"])
            new_message = self.gpgmail.sign(draft)
            if new_message:
                self.gmail.send(bundle["id"], new_message)
                result = True
        except Exception, e:
            self.logger.exception(e)
        finally:
            return result
