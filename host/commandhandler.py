from gpgmail import GPGMail
from gmail import GMail


class CommandHandler(object):

    def __init__(self):
        self.gmail = GMail()
        self.gpgmail = GPGMail()

    def parse(self, message):
        result = None
        if message["command"] == 'verify':
            result = self.verify(message)
        elif message["command"] == 'sign':
            result = self.sign(message)
        return result

    def verify(self, message):
        mail = self.gmail.get(message["id"])
        return self.gpgmail.verify(mail)

    def sign(self, message):
        draft = self.gmail.get(message["id"])
        new_message = self.gpgmail.sign(draft)
        #return self.verify(message)
        #self.gmail.send(message["id"], new_message, delete_draft=True)
        return new_message



if __name__ == '__main__':
    import json
    h = CommandHandler()
    # v = {"command": "verify"}
    # v['id'] = "145f1ee82379fe8d"  # in line
    # v['id'] = "145f209c26d573f4"  # attached
    # result = h.parse(v)
    # print json.dumps(result)

    v = {"command": "sign"}
    v['id'] = "1495c4690857a02b"
    v['id'] = '1495c27cf9211a92' # with attached
    result = h.parse(v)
    #print json.dumps(result)
