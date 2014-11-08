#!/usr/bin/env python
from xdg import BaseDirectory

import struct
import sys
import json
import logging
import os

from util import StreamToLogger
from commandhandler import CommandHandler


def send_message(message):
    """Helper function that sends a message to the webapp."""
    # Get a json string from the message
    message = json.dumps(message)
    # Write message size.
    sys.stdout.write(struct.pack('I', len(message)))
    # Write the message itself.
    sys.stdout.write(message)
    sys.stdout.flush()


def read_message():
    """Helper that reads messages from the webapp."""
    # Read the message length (first 4 bytes).
    text_length_bytes = sys.stdin.read(4)

    # Unpack message length as 4 byte integer.
    text_length = struct.unpack('i', text_length_bytes)[0]

    # Read the text (JSON object) of the message.
    raw_text = sys.stdin.read(text_length).decode('utf-8')
    return json.loads(raw_text)


def main():
    """Thread that reads messages from the webapp."""
    filelog = os.path.join(BaseDirectory.save_cache_path('goopg'), 'log')
    logging.basicConfig(filename=filelog,
                        filemode='a',
                        level=logging.ERROR,
                        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    # redirect stderr to logger
    sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)
    handler = CommandHandler()

    # send init request
    send_message({"command": "request_init"})

    # a queue to store messages received before the 'init' bundle
    queue_messages = []
    while 1:
        try:
            bundle = read_message()
        except struct.error, e:
            logging.error("Error while reading stdin: \"{}\""
                          " - Exit.".format(e.message))
            sys.exit(1)
        if not handler.initialized and bundle['command'] != 'init':
            queue_messages.append(bundle)
        else:
            def parse_and_send_result(b):
                result = handler.parse(b)
                if result is not None:
                    b['result'] = result
                    send_message(b)

            parse_and_send_result(bundle)

            if len(queue_messages) > 0:
                for bundle in queue_messages:
                    parse_and_send_result(bundle)
                queue_messages = []


if __name__ == '__main__':
    main()
    sys.exit(0)
