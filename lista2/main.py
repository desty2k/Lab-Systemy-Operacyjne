"""
Simulation for disk scheduling algorithms.
One tick = moved over one cylinder.
"""

import copy
import pickle
import random
import logging
import operator
import collections

from utils import Logger, threaded
from request import Request

LOGGING_LEVEL = logging.INFO
PICKLED_FILENAME = "requests.pick"

START_POS = 0
DISK_SIZE = 5000
REQUESTS_COUNT = 2500

MIN_ARRIVE_TIME = 0
MAX_ARRIVE_TIME = 25000

REAL_TIME_COUNT = 5000
MIN_DEADLINE = 0
MAX_DEADLINE = 500


class Main:
    def __init__(self):
        super(Main, self).__init__()
        self.que = []

    def create_requests(self) -> None:
        """Fills queue with disk access requests."""
        for x in range(REQUESTS_COUNT - REAL_TIME_COUNT):
            self.que.append(Request(random.randint(MIN_ARRIVE_TIME, MAX_ARRIVE_TIME),
                                    random.randint(0, DISK_SIZE)))

        for x in range(REAL_TIME_COUNT):
            self.que.append(Request(random.randint(MIN_ARRIVE_TIME, MAX_ARRIVE_TIME),
                                    random.randint(0, DISK_SIZE),
                                    real_time=True, deadline=random.randint(MIN_DEADLINE, MAX_DEADLINE)))

        self.que.sort(key=lambda req: req.arrive_time)
        for index, request in enumerate(self.que):
            request.set_id(index + 1)

    def save_processes_to_file(self) -> None:
        """Saves requests to file using pickle."""
        with open(PICKLED_FILENAME, "wb") as file:
            pickle.dump(self.que, file)

    def load_processes_from_file(self) -> None:
        """Load requests from files using pickle."""
        with open(PICKLED_FILENAME, "rb") as file:
            self.que = pickle.load(file)

    @threaded
    def run_fcfs(self):
        logger = logging.getLogger("FCFS")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = START_POS
        time = incomming[0].arrive_time

        while True:
            for request in list(incomming):
                if request.arrive_time <= time:
                    incomming.remove(request)
                    queue.append(request)

            if len(queue) != 0:
                request = queue.popleft()
                # processes are sorted by arrive time so we do not have search for min
                # request: Request = min(queue, key=operator.attrgetter("arrive_time"))
                # queue.remove(request)
                completed.append(request)

                # calculate delta of head position and add it to time
                delta = abs(current_pos - request.cylinder)
                current_pos = request.cylinder
                time = time + delta

                for other in list(queue):
                    other.add_wait_time(delta)

            if len(incomming) == 0 and len(queue) == 0:
                break

        longest_waiting = max(completed, key=operator.attrgetter("wait_time"))
        logger.info("================= FCFS =================")
        logger.info("Average waiting time: {}".format(round(sum(req.wait_time for req in completed) /
                                                            len(completed), 2)))
        logger.info("Request with longest waiting time ID: {}, Time: {}, Cylinder: {}, Arrived: {}".
                    format(longest_waiting.request_id,
                           longest_waiting.wait_time,
                           longest_waiting.cylinder,
                           longest_waiting.arrive_time))

    @threaded
    def run_sstf(self):
        logger = logging.getLogger("SSTF")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = START_POS
        time = incomming[0].arrive_time

        while True:
            for request in list(incomming):
                if request.arrive_time <= time:
                    queue.append(request)
                    incomming.remove(request)

            if len(queue) != 0:
                nearest: Request = min(queue, key=lambda req: abs(current_pos - req.cylinder))
                queue.remove(nearest)
                completed.append(nearest)

                # calculate delta of head position and add it to time
                delta = abs(current_pos - nearest.cylinder)
                current_pos = nearest.cylinder
                time = time + delta

                for other in list(queue):
                    other.add_wait_time(delta)

            if len(incomming) == 0 and len(queue) == 0:
                break

        longest_waiting = max(completed, key=operator.attrgetter("wait_time"))
        logger.info("================= SSTF =================")
        logger.info("High starvation rate for requests on \"edges\" of disk.")
        logger.info("Average waiting time: {}".format(round(sum(req.wait_time for req in completed) /
                                                            len(completed), 2)))
        logger.info("Request with longest waiting time ID: {}, Time: {}, Cylinder: {}, Arrived: {}".
                    format(longest_waiting.request_id,
                           longest_waiting.wait_time,
                           longest_waiting.cylinder,
                           longest_waiting.arrive_time))

    @threaded
    def run_scan(self):
        logger = logging.getLogger("SCAN")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = START_POS
        # check on which side first request is
        # to_right = True
        to_right = incomming[0].cylinder >= current_pos
        time = 0

        while True:
            for request in list(incomming):
                if request.arrive_time <= time:
                    queue.append(request)
                    incomming.remove(request)

            # decrease disc size and max arrive time to generate more interesting results
            for request_in_cylinder in [req for req in queue if req.cylinder == current_pos]:
                logger.debug("Request {} scaned on pos {}".format(request_in_cylinder.request_id,
                                                                  request_in_cylinder.cylinder))
                queue.remove(request_in_cylinder)
                completed.append(request_in_cylinder)

            time = time + 1
            if to_right:
                if current_pos == DISK_SIZE:
                    to_right = False
                else:
                    current_pos = current_pos + 1
            else:
                if current_pos == 0:
                    to_right = True
                else:
                    current_pos = current_pos - 1

            for other in list(queue):
                other.add_wait_time(1)

            if len(incomming) == 0 and len(queue) == 0:
                break

        longest_waiting = max(completed, key=operator.attrgetter("wait_time"))
        logger.info("================= SCAN =================")
        logger.info("Average waiting time: {}".format(round(sum(req.wait_time for req in completed) /
                                                            len(completed), 2)))
        logger.info("Request with longest waiting time ID: {}, Time: {}, Cylinder: {}, Arrived: {}".
                    format(longest_waiting.request_id,
                           longest_waiting.wait_time,
                           longest_waiting.cylinder,
                           longest_waiting.arrive_time))

    @threaded
    def run_c_scan(self):
        logger = logging.getLogger("C-SCAN")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = START_POS
        time = 0

        while True:
            for request in list(incomming):
                if request.arrive_time <= time:
                    queue.append(request)
                    incomming.remove(request)

            for request_in_cylinder in [req for req in queue if req.cylinder == current_pos]:
                logger.debug("Request {} scaned on pos {}".format(request_in_cylinder.request_id,
                                                                  request_in_cylinder.cylinder))
                queue.remove(request_in_cylinder)
                completed.append(request_in_cylinder)

            time = time + 1
            if current_pos == DISK_SIZE:
                # time = time + current_pos
                current_pos = 0
            else:
                current_pos = current_pos + 1

            for other in list(queue):
                other.add_wait_time(1)

            if len(incomming) == 0 and len(queue) == 0:
                break

        longest_waiting = max(completed, key=operator.attrgetter("wait_time"))
        logger.info("================= C-SCAN =================")
        logger.info("Average waiting time: {}".format(round(sum(req.wait_time for req in completed) /
                                                            len(completed), 2)))
        logger.info("Request with longest waiting time ID: {}, Time: {}, Cylinder: {}, Arrived: {}".
                    format(longest_waiting.request_id,
                           longest_waiting.wait_time,
                           longest_waiting.cylinder,
                           longest_waiting.arrive_time))

    @threaded
    def run_c_look(self):
        logger = logging.getLogger("C-LOOK")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = START_POS
        time = 0

        while True:
            for request in list(incomming):
                if request.arrive_time <= time:
                    queue.append(request)
                    incomming.remove(request)

            for request_in_cylinder in [req for req in queue if req.cylinder == current_pos]:
                logger.debug("Request {} scaned on pos {}".format(request_in_cylinder.request_id,
                                                                  request_in_cylinder.cylinder))
                queue.remove(request_in_cylinder)
                completed.append(request_in_cylinder)

            time = time + 1
            if current_pos == DISK_SIZE:
                requests_cylinders = [req.cylinder for req in queue]
                if requests_cylinders:
                    current_pos = min(requests_cylinders)
                else:
                    current_pos = 0
                logger.debug("Going back to pos {}".format(current_pos))
            else:
                if len([req for req in queue if req.cylinder in range(current_pos, DISK_SIZE + 1)]) == 0:
                    current_pos = DISK_SIZE
                else:
                    current_pos = current_pos + 1
                    for other in list(queue):
                        other.add_wait_time(1)

            if len(incomming) == 0 and len(queue) == 0:
                break

        longest_waiting = max(completed, key=operator.attrgetter("wait_time"))
        logger.info("================= C-LOOK =================")
        logger.info("Average waiting time: {}".format(round(sum(req.wait_time for req in completed) /
                                                            len(completed), 2)))
        logger.info("Request with longest waiting time ID: {}, Time: {}, Cylinder: {}, Arrived: {}".
                    format(longest_waiting.request_id,
                           longest_waiting.wait_time,
                           longest_waiting.cylinder,
                           longest_waiting.arrive_time))

    @threaded
    def run_sstf_edf(self):
        logger = logging.getLogger("SSTF-EDF")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = START_POS
        time = incomming[0].arrive_time

        while True:
            for request in list(incomming):
                if request.arrive_time <= time:
                    queue.append(request)
                    incomming.remove(request)

            if len(queue) != 0:
                # check for real time requests
                real_time = [req for req in queue if req.real_time]
                if len(real_time) > 0:
                    # find shortest real time request
                    nearest = min(real_time, key=operator.attrgetter("deadline"))
                else:
                    # fallback to sstf
                    nearest: Request = min(queue, key=lambda req: abs(current_pos - req.cylinder))

                queue.remove(nearest)
                completed.append(nearest)

                # calculate delta of head position and add it to time
                delta = abs(current_pos - nearest.cylinder)
                current_pos = nearest.cylinder
                time = time + delta

                for other in list(queue):
                    other.add_wait_time(delta)

            if len(incomming) == 0 and len(queue) == 0:
                break

        longest_waiting = max(completed, key=operator.attrgetter("wait_time"))
        logger.info("================= SSTF-EDF =================")
        logger.info("Switches to FCFS if real time requests arrive.")
        logger.info("Average waiting time: {}".format(round(sum(req.wait_time for req in completed) /
                                                            len(completed), 2)))
        logger.info("Request with longest waiting time ID: {}, Time: {}, Cylinder: {}, Arrived: {}, Real-time: {}".
                    format(longest_waiting.request_id,
                           longest_waiting.wait_time,
                           longest_waiting.cylinder,
                           longest_waiting.arrive_time,
                           longest_waiting.real_time))

    @threaded
    def run_sstf_fdf_scan(self):
        logger = logging.getLogger("SSTF-FDF-SCAN")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = START_POS
        time = incomming[0].arrive_time
        target = None

        while True:
            for request in list(incomming):
                if request.arrive_time <= time:
                    queue.append(request)
                    incomming.remove(request)

            logger.debug("POS: {} QUEUE: {}".format(current_pos, [str(req.cylinder) + "*" if req.real_time
                                                                  else str(req.cylinder) for req in queue]))
            if len(queue) != 0:
                if target:
                    if target.cylinder == current_pos:
                        logger.debug("Head over target cylinder {}".format(current_pos))
                        queue.remove(target)
                        completed.append(target)
                        target = None
                    else:
                        for request_in_cylinder in [req for req in queue if req.cylinder == current_pos]:
                            logger.debug("Request {} scaned on pos {}".format(request_in_cylinder.request_id,
                                                                              request_in_cylinder.cylinder))
                            queue.remove(request_in_cylinder)
                            completed.append(request_in_cylinder)

                        time = time + 1
                        if current_pos < target.cylinder:
                            current_pos = current_pos + 1
                        else:
                            current_pos = current_pos - 1
                        time = time + 1
                        for other in list(queue):
                            other.add_wait_time(1)

                else:
                    # no target, check for new real time requests
                    real_time = [req for req in queue if req.real_time]
                    if len(real_time) > 0:
                        nearest_realtime: Request = min(real_time, key=operator.attrgetter("deadline"))
                        if nearest_realtime.deadline >= abs(current_pos - nearest_realtime.cylinder):
                            target = nearest_realtime
                            logger.debug("Target set to request {}, Deadline {} >= Delta pos {}"
                                         .format(nearest_realtime.cylinder, nearest_realtime.deadline,
                                                 abs(current_pos - nearest_realtime.cylinder)))
                        else:
                            # request too far, fallback to sstf
                            logger.debug("Not worth to process request {}, Deadline: {} < Delta pos {}"
                                         .format(nearest_realtime.cylinder, nearest_realtime.deadline,
                                                 abs(current_pos - nearest_realtime.cylinder)))
                            nearest: Request = min(queue, key=lambda req: abs(current_pos - req.cylinder))
                            queue.remove(nearest)
                            completed.append(nearest)

                            # calculate delta of head position and add it to time
                            delta = abs(current_pos - nearest.cylinder)
                            current_pos = nearest.cylinder
                            time = time + delta

                            for other in list(queue):
                                other.add_wait_time(delta)
                    else:
                        # no real time requests, fallback to sstf
                        nearest: Request = min(queue, key=lambda req: abs(current_pos - req.cylinder))
                        queue.remove(nearest)
                        completed.append(nearest)

                        # calculate delta of head position and add it to time
                        delta = abs(current_pos - nearest.cylinder)
                        current_pos = nearest.cylinder
                        time = time + delta

                        for other in list(queue):
                            other.add_wait_time(delta)

            if len(incomming) == 0 and len(queue) == 0:
                break

        longest_waiting = max(completed, key=operator.attrgetter("wait_time"))
        logger.info("================= SSTF-FDF-SCAN =================")
        logger.info("Switches to SCAN if real time requests arrive.")
        logger.info("Average waiting time: {}".format(round(sum(req.wait_time for req in completed) /
                                                            len(completed), 2)))
        logger.info("Request with longest waiting time ID: {}, Time: {}, Cylinder: {}, Arrived: {}, Real-time: {}".
                    format(longest_waiting.request_id,
                           longest_waiting.wait_time,
                           longest_waiting.cylinder,
                           longest_waiting.arrive_time,
                           longest_waiting.real_time))


if __name__ == '__main__':
    log = Logger()
    log.enable()
    log.set_level(LOGGING_LEVEL)

    main_logger = logging.getLogger()
    main_logger.info("Head start position is {}".format(START_POS))
    main_logger.info("Disk size is {}".format(DISK_SIZE))
    main_logger.info("Total request count is {}".format(REQUESTS_COUNT))
    main_logger.info("Real time request count is {}".format(REAL_TIME_COUNT))

    m = Main()
    m.create_requests()
    m.save_processes_to_file()
    # m.load_processes_from_file()

    threads = []
    for attr in dir(m):
        if attr.startswith("run"):
            threads.append(getattr(m, attr)())

    for thread in threads:
        thread.join()
