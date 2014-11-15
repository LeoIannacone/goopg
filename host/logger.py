import logging
import os
import sys

from xdg import BaseDirectory


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    Adapted from: http://bit.ly/1xLpNuF
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(*arg):
        pass


class GoopgLogger(object):
    """
    A simple class wich configure the basic logger
    """
    filelog = os.path.join(BaseDirectory.save_cache_path('goopg'), 'log')
    logging.basicConfig(filename=filelog,
                        filemode='a',
                        level=logging.ERROR,
                        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    # redirect stderr to logger
    sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)
