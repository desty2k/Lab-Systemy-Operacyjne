"""
https://stackoverflow.com/questions/8097408/why-python-is-so-slow-for-a-simple-for-loop
"""

import copy
import pickle
import random
import logging
import operator
import collections

from Process import Process
from Utils import OutputLogger

PROCESSES_FILENAME = "procs_data.txt"
PROCESS_COUNT = 5000
PROCESS_SWITCH_DELAY = 1
RR_QUANTUM_TIME = 30
MIN_PROCESS_LENGTH = 5
MAX_PROCESS_LENGTH = 21
STARVATION_THRESHOLD = 80000

# zagłodzenie - starvation


class Main:
    def __init__(self):
        super(Main, self).__init__()
        self.que = []

    def create_processes(self, count):
        for x in range(count):
            # self.que.append(
            #     Process(x, round(gauss_distribution(100, 50, 0, 1000)),
            #             round(gauss_distribution(100, 50, 5, 25))))
            self.que.append(
                Process(x, random.randint(0, 1000),
                        random.randint(MIN_PROCESS_LENGTH, MAX_PROCESS_LENGTH)))
        self.que.sort(key=lambda proc: proc.arrive_time)

    def save_processes_to_file(self):
        with open(PROCESSES_FILENAME, "wb") as file:
            pickle.dump(self.que, file)

    def load_processes_from_file(self):
        with open(PROCESSES_FILENAME, "rb") as file:
            self.que = pickle.load(file)

    def runFCFS(self):
        logger = logging.getLogger("FCFS")
        incomming = collections.deque(copy.deepcopy(self.que))
        completed = collections.deque()
        starved_processes = collections.deque()
        queue = collections.deque()
        time = 0

        while True:
            # check for new processes
            for process in list(incomming):
                if process.arrive_time <= time:
                    queue.append(process)
                    incomming.remove(process)

            if len(queue) != 0:
                process = queue.popleft()
                process.set_time_left(0)
                completed.append(process)

                for other in list(queue):
                    if other.time_waiting >= STARVATION_THRESHOLD:
                        starved_processes.append(other)
                        queue.remove(other)
                    else:
                        other.set_wait_time(other.time_waiting + process.duration)

                time = time + process.duration
            if len(incomming) == 0 and len(queue) == 0:
                break

        longest_waiting = max(completed, key=operator.attrgetter("time_waiting"))
        logger.info("================= FCFS =================")
        logger.info("Total starved processes: {}".format(len(starved_processes)))
        logger.info("Average waiting time: {}".format(round(sum(proc.time_waiting for proc in completed) /
                                                            len(completed), 2)))
        logger.info("Longest waiting time: {}, Duration: {}, Arrived: {}".format(longest_waiting.time_waiting,
                                                                                 longest_waiting.duration,
                                                                                 longest_waiting.arrive_time))

    def runSJF(self):
        logger = logging.getLogger("SJF")
        time = 0
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        starved_processes = collections.deque()
        total_switch_time = 0
        previous_process_id = None

        while True:
            for proc in list(incomming):
                if proc.arrive_time <= time:
                    queue.append(proc)
                    incomming.remove(proc)
                else:
                    proc.set_wait_time(time)

            if len(queue) > 0:
                shortest: Process = min(queue, key=operator.attrgetter("time_left"))
                shortest.set_time_left(shortest.time_left - 1)
                # print([x.time_left for x in queue])
                queue.remove(shortest)

                # sorting gives same result but real computing time is higher
                # queue = collections.deque(sorted(queue, key=operator.attrgetter("time_left")))
                # shortest: Process = queue.popleft()
                # shortest.set_time_left(shortest.time_left - 1)

                for proc in list(queue):
                    if proc.time_waiting >= STARVATION_THRESHOLD:
                        starved_processes.append(proc)
                        queue.remove(proc)
                    else:
                        proc.set_wait_time(time + 1)

                if shortest.time_left > 0:
                    queue.insert(0, shortest)
                else:
                    completed.append(shortest)

                if previous_process_id and previous_process_id != shortest.id:
                    total_switch_time = total_switch_time + PROCESS_SWITCH_DELAY
                previous_process_id = shortest.id

            time = time + 1
            if len(incomming) == 0 and len(queue) == 0:
                break

        longest_waiting = max(completed, key=operator.attrgetter("time_waiting"))
        logger.info("================= SJF =================")
        logger.info("Switch delay was {}".format(PROCESS_SWITCH_DELAY))
        logger.info("Total starved processes: {}".format(len(starved_processes)))
        logger.info("Time wasted for switching: {}".format(round(total_switch_time, 2)))
        logger.info("Average waiting time: {}".format(sum(proc.time_waiting for proc in completed) / len(completed)))
        logger.info("Longest waiting time: {}, Duration: {}, Arrived: {}".format(longest_waiting.time_waiting,
                                                                                 longest_waiting.duration,
                                                                                 longest_waiting.arrive_time))

    def runRR(self):
        logger = logging.getLogger("RR")
        time = 0
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        starved_processes = collections.deque()
        total_switch_time = 0

        while True:
            # check for new processes
            for process in list(incomming):
                if process.arrive_time <= time:
                    queue.append(process)
                    incomming.remove(process)

            if len(queue) != 0:
                process = queue.popleft()
                time_delta = process.time_left - RR_QUANTUM_TIME
                if time_delta <= 0:
                    process.set_time_left(0)
                    completed.append(process)
                    time_delta = process.duration - process.time_left
                else:
                    process.set_time_left(time_delta)

                for other in list(queue):
                    if other.time_waiting >= STARVATION_THRESHOLD:
                        starved_processes.append(other)
                        queue.remove(other)
                    else:
                        other.set_wait_time(other.time_waiting + time_delta)

                if process.time_left != 0:
                    queue.append(process)

                time = time + time_delta + PROCESS_SWITCH_DELAY
                total_switch_time = total_switch_time + PROCESS_SWITCH_DELAY
            if len(incomming) == 0 and len(queue) == 0:
                break

        longest_waiting = max(completed, key=operator.attrgetter("time_waiting"))
        logger.info("================= RR =================")
        logger.info("Time quant was {} ({}% of maximum process length).".format(
            RR_QUANTUM_TIME, round(100 * RR_QUANTUM_TIME/MAX_PROCESS_LENGTH)))
        logger.info("Switch delay was {}".format(PROCESS_SWITCH_DELAY))
        logger.info("Total starved processes: {}".format(len(starved_processes)))
        logger.info("Time wasted for switching: {}".format(round(total_switch_time, 2)))
        logger.info("Average waiting time: {}".format(round(sum(proc.time_waiting for proc in completed) /
                                                            len(completed), 2)))
        logger.info("Longest waiting time: {}, Duration: {}, Arrived: {}".format(longest_waiting.time_waiting,
                                                                                 longest_waiting.duration,
                                                                                 longest_waiting.arrive_time))


if __name__ == '__main__':
    log = OutputLogger()
    logger = logging.getLogger()
    logger.info("Increase starvation threshold to show longest waiting processes.")
    logger.info("Increase quant of time to make RR work as FCFS.")
    logger.info("RR runs fastest when quant of time is greater than 80% of process length.")

    main = Main()
    # main.create_processes(PROCESS_COUNT)
    # main.save_processes_to_file()
    main.load_processes_from_file()
    main.runFCFS()
    main.runSJF()
    main.runRR()
