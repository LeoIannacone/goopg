#!/usr/bin/env python

import logging
import sys

from urlparse import urlparse, parse_qs
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from json import dumps

from logger import GoopgLogger
from commandhandler import CommandHandler


PORT = 40094


class GoopgHandler(BaseHTTPRequestHandler):

    #Handler for the GET requests
    def do_GET(self):
        if self.path == '/favicon.ico':
            self.send_response(404)
            return

        bundle = self.from_path_to_bundle()

        if not 'command' in bundle:
            self.send_response(400)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        initialized = self.server.handler.initialized

        if initialized is False and bundle['command'] != 'init':
            bundle = {"command": "request_init"}
            self.wfile.write(dumps(bundle, indent=4))
            return

        bundle['result'] = self.server.handler.parse(bundle)
        self.wfile.write(dumps(bundle, indent=4))
        return

    def from_path_to_bundle(self):
        """
        Parse the path and returns the bundle
        """
        bundle = {}
        url = urlparse(self.path)
        query = parse_qs(url.query)
        # query is a dict of keys and values (list), so keep only the
        # first value
        for k in query:
            bundle[k] = query[k].pop()
        return bundle


class GoopgHTTPServer(HTTPServer):

    def __init__(self, host, request_handler):
        self.handler = CommandHandler()
        self.logger = logging.getLogger('http-main')
        HTTPServer.__init__(self, host, request_handler)


def main():
    GoopgLogger()
    #Create a web server and define the handler to manage the
    #incoming request
    server = GoopgHTTPServer(('127.0.0.1', PORT), GoopgHandler)

    #Wait forever for incoming http requests
    server.serve_forever()


if __name__ == '__main__':
    main()
    sys.exit(0)
