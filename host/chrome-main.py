#!/usr/bin/env python

import struct
import sys
import json
import logging

from commandhandler import CommandHandler
from logger import GoopgLogger


def send_bundle(bundle):
    """Helper function that sends a bundle to the webapp."""
    # Get a json string from the bundle
    bundle = json.dumps(bundle)
    # Write bundle size.
    sys.stdout.write(struct.pack('I', len(bundle)))
    # Write the bundle itself.
    sys.stdout.write(bundle)
    sys.stdout.flush()


def read_bundle():
    """Helper that reads bundles from the webapp."""
    # Read the bundle length (first 4 bytes).
    text_length_bytes = sys.stdin.read(4)

    # Unpack bundle length as 4 byte integer.
    text_length = struct.unpack('i', text_length_bytes)[0]

    # Read the text (JSON object) of the bundle.
    raw_text = sys.stdin.read(text_length).decode('utf-8')
    return json.loads(raw_text)


def main():
    """Thread that reads messages from the webapp."""
    GoopgLogger()
    handler = CommandHandler()

    # a queue to store bundles received before the 'init' command
    queue = []
    while 1:
        try:
            bundle = read_bundle()
        except struct.error, e:
            logger.error("Error while reading stdin: \"{}\""
                         " - Exit.".format(e.message))
            sys.exit(1)
        if not handler.initialized and bundle['command'] != 'init':
            # send init request
            send_bundle({"command": "request_init"})
            queue.append(bundle)
        else:
            def parse_and_send_result(b):
                result = handler.parse(b)
                if result is not None:
                    b['result'] = result
                    send_bundle(b)

            parse_and_send_result(bundle)

            if len(queue) > 0:
                for bundle in queue:
                    parse_and_send_result(bundle)
                queue = []

logger = logging.getLogger('chrome-main')

if __name__ == '__main__':
    try:
        main()
    except e:
        logger.error("General error: {}".format(e.message))
    sys.exit(0)
