import logging


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
