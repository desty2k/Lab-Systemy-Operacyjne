"""
ilość pamięci
ilośc ramek
max długość ciągu lokalnego
podzbiór dla lokalności (np 3, 5, 10)
jak często występuje lokalność odwołań
"""
from qtpy.QtCore import QObject, qInstallMessageHandler

import sys
import copy
import pickle
import random
import logging
import operator
import traceback
import collections

from utils import Logger, qt_message_handler
from request import Request

REQUESTS_COUNT = 2000
PHYSICAL_MEMORY = 5
VIRTUAL_MEMORY = 20
LOCAL_REQUESTS_MAX_LENGTH = 10
LOCAL_REQUESTS_MAX_DELTA = 1
LOCAL_REQUESTS_CHANCE = 5  # range 1-10 | *10% chance of generating local requests sequence

LOGGING_LEVEL = logging.INFO
PICKLED_FILENAME = "requests.pick"


class Main(QObject):

    def __init__(self):
        super(Main, self).__init__()
        self.que = []

    def create_requests(self) -> None:
        """Fills queue with disk access requests."""
        arrive_time = 1
        while arrive_time != REQUESTS_COUNT + 1:
            if random.randint(0, 10) < LOCAL_REQUESTS_CHANCE:
                # generate sequence of local request
                local_length = random.randint(1, LOCAL_REQUESTS_MAX_LENGTH)
                local_mid_page = random.randint(1, VIRTUAL_MEMORY + 1)
                for i in range(local_length):
                    if arrive_time >= REQUESTS_COUNT + 1:
                        break
                    while True:
                        # generate random page and check if it exists in memory
                        local_page = local_mid_page + random.randint(-LOCAL_REQUESTS_MAX_DELTA,
                                                                     LOCAL_REQUESTS_MAX_DELTA)
                        if local_page in range(1, VIRTUAL_MEMORY + 1):
                            break
                    self.que.append(Request(local_page, arrive_time, local=True))
                    arrive_time = arrive_time + 1

            else:
                # generate one random request
                self.que.append(Request(random.randint(1, VIRTUAL_MEMORY + 1), arrive_time))
                arrive_time = arrive_time + 1

    def save_processes_to_file(self) -> None:
        """Saves requests to file using pickle."""
        with open(PICKLED_FILENAME, "wb") as file:
            pickle.dump(self.que, file)

    def load_processes_from_file(self) -> None:
        """Load requests from files using pickle."""
        with open(PICKLED_FILENAME, "rb") as file:
            self.que = pickle.load(file)

    def print_requests(self):
        logging.getLogger("GENERATOR").info([str(req) for req in self.que])

    def run_FIFO(self):
        logger = logging.getLogger("FIFO")
        frames = [None] * PHYSICAL_MEMORY
        page_faults = 0
        incomming = collections.deque(copy.deepcopy(self.que))
        completed = collections.deque()

        while True:
            request: Request = incomming.popleft()
            if request.get_page() not in [req.get_page() for req in frames if req is not None]:
                page_faults += 1
                if any(req is None for req in frames):
                    frames[frames.index(None)] = request
                    continue
                longest_staying: Request = min(frames, key=operator.attrgetter("arrive_time"))
                frames[frames.index(longest_staying)] = request

            completed.append(request)
            if len(incomming) == 0:
                break
        logger.info("================= FIFO =================")
        logger.info("Page faults {}".format(page_faults))
        logger.info("Frames after running algorithm {}".format([req.get_page() for req in frames]))

    def run_OPT(self):
        logger = logging.getLogger("OPT")
        frames = [None] * PHYSICAL_MEMORY
        page_faults = 0
        incomming = collections.deque(copy.deepcopy(self.que))
        completed = collections.deque()

        while True:
            request: Request = incomming.popleft()
            if request.get_page() not in [req.get_page() for req in frames if req is not None]:
                page_faults += 1
                if any(req is None for req in frames):
                    frames[frames.index(None)] = request
                    continue

                used_frames = {req.get_page(): 0 for req in frames if req is not None}
                for awaiting in incomming:
                    awaiting_page = awaiting.get_page()
                    if awaiting_page in used_frames and used_frames.get(awaiting_page) == 0:
                        used_frames[awaiting_page] = awaiting.get_arrive_time()
                max_page = max(used_frames, key=used_frames.get)
                for index, frame in enumerate(frames):
                    if frame is not None and frame.get_page() == max_page:
                        frames[index] = request

            completed.append(request)
            if len(incomming) == 0:
                break

        logger.info("================= OPT =================")
        logger.info("Page faults {}".format(page_faults))
        logger.info("Frames after running algorithm {}".format([req.get_page() for req in frames]))

    def run_LRU(self):
        logger = logging.getLogger("LRU")
        frames = [None] * PHYSICAL_MEMORY
        page_faults = 0
        incomming = collections.deque(copy.deepcopy(self.que))
        completed = collections.deque()

        while True:
            request: Request = incomming.popleft()
            if request.get_page() not in [req.get_page() for req in frames if req is not None]:
                page_faults += 1
                if any(req is None for req in frames):
                    frames[frames.index(None)] = request
                    continue
                lru = min(frames, key=lambda f: f.get_last_used_time())
                frames[frames.index(lru)] = request
            else:
                for frame in frames:
                    if frame and frame.get_page() == request.get_page():
                        frame.set_last_used_time(request.get_last_used_time())

            completed.append(request)
            if len(incomming) == 0:
                break

        logger.info("================= LRU =================")
        logger.info("Page faults {}".format(page_faults))
        logger.info("Frames after running algorithm {}".format([req.get_page() for req in frames]))

    def run_SC(self):
        logger = logging.getLogger("SC")
        frames = [None] * PHYSICAL_MEMORY
        page_faults = 0
        incomming = collections.deque(copy.deepcopy(self.que))
        completed = collections.deque()
        fifo = collections.deque(maxlen=PHYSICAL_MEMORY)

        while True:
            request: Request = incomming.popleft()
            if request.get_page() not in [req.get_page() for req in frames if req is not None]:
                page_faults += 1
                if any(req is None for req in frames):
                    frames[frames.index(None)] = request
                    fifo.append(request)
                    continue
                while fifo[0].get_recall_byte() != 0:
                    req = fifo.popleft()
                    req.set_recall_byte(0)
                    fifo.append(req)
                req = fifo.popleft()
                fifo.append(request)
                frames[frames.index(req)] = request

            completed.append(request)
            if len(incomming) == 0:
                break

        logger.info("================= SC =================")
        logger.info("Page faults {}".format(page_faults))
        logger.info("Frames after running algorithm {}".format([req.get_page() for req in frames]))

    def run_RAND(self):
        logger = logging.getLogger("RAND")
        frames = [None] * PHYSICAL_MEMORY
        page_faults = 0
        incomming = collections.deque(copy.deepcopy(self.que))
        completed = collections.deque()

        while True:
            request: Request = incomming.popleft()
            if request.get_page() not in [req.get_page() for req in frames if req is not None]:
                page_faults += 1
                if any(req is None for req in frames):
                    frames[frames.index(None)] = request
                    continue
                frames[random.randint(0, len(frames) - 1)] = request
            completed.append(request)
            if len(incomming) == 0:
                break
        logger.info("================= RAND =================")
        logger.info("Page faults {}".format(page_faults))
        logger.info("Frames after running algorithm {}".format([req.get_page() for req in frames]))


if __name__ == '__main__':
    log = Logger()
    log.enable()
    log.set_level(LOGGING_LEVEL)

    qInstallMessageHandler(qt_message_handler)
    def exception_hook(exctype, value, tb):
        logging.critical(''.join(traceback.format_exception(exctype, value, tb)))
        sys.exit(1)
    sys.excepthook = exception_hook

    m = Main()
    m.create_requests()
    m.print_requests()
    m.run_FIFO()
    m.run_OPT()
    m.run_LRU()
    m.run_SC()
    m.run_RAND()
