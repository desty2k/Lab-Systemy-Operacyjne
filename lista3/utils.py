import logging
import threading
import functools
import coloredlogs
from qtpy.QtCore import QtInfoMsg, QtWarningMsg, QtCriticalMsg


def qt_message_handler(mode, context, message):
    logger = logging.getLogger("QT Logger")
    """Qt errors handler"""
    if mode == QtInfoMsg:
        mode = 20
    elif mode == QtWarningMsg:
        mode = 30
    elif mode == QtCriticalMsg:
        mode = 40
    elif mode == QtCriticalMsg:
        mode = 50
    else:
        mode = 20
    logger.log(mode, "(%s: %s): %s" % (context.file, context.line, message))


class Logger:
    def __init__(self, ):
        super(Logger, self).__init__()
        self.logger = None
        self.handler = None
        self.formatter = None

    def enable(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.NOTSET)

        self.handler = logging.StreamHandler()
        self.handler.setLevel(logging.NOTSET)

        self.formatter = coloredlogs.ColoredFormatter("%(asctime)s "
                                                      "[%(threadName)s] "
                                                      "[%(name)s] "
                                                      "[%(levelname)s] "
                                                      "%(message)s")
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        self.logger.info("Logger enabled")
        return self.logger

    def set_level(self, level):
        if self.logger and self.handler:
            self.logger.setLevel(level)
            self.handler.setLevel(level)
        else:
            raise Exception("Logger not enabled!")


class TaskThread(threading.Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        super(TaskThread, self).__init__(group, target, name, args, kwargs, daemon=daemon)
        self.result = None
        self.exit_code = None

    def run(self):
        if self._target is not None:
            try:
                self.result = self._target(*self._args, **self._kwargs)
                self.exit_code = 0
            except Exception as e:
                self.result = e
                self.exit_code = 1

    def join(self, timeout=None):
        threading.Thread.join(self, timeout)
        return {"result": self.result, "exit_code": self.exit_code}


def threaded(function):
    """Move function to thread.
    functools.wraps copies __name__ and __doc__ from wrapped function. """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        thread = TaskThread(target=function, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper
