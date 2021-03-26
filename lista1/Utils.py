import random
import logging
import coloredlogs


class OutputLogger:
    """Logging cocfiguration class"""

    def __init__(self):
        super(OutputLogger, self).__init__()
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.NOTSET)
        self.handler = logging.StreamHandler()
        self.handler.setLevel(logging.NOTSET)

        self.formatter = coloredlogs.ColoredFormatter("%(asctime)s [%(threadName)s] [%(name)s] [%(levelname)s] %("
                                                      "message)s")
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

        notify = logging.getLogger(self.__class__.__name__)
        notify.info("Logger enabled")

    def setLevel(self, level: int):
        self.logger.setLevel(level)
        self.handler.setLevel(level)


def gauss_distribution(mu, sigma, bottom, top):
    a = random.gauss(mu, sigma)
    while not (bottom <= a <= top):
        a = random.gauss(mu, sigma)
    return a
