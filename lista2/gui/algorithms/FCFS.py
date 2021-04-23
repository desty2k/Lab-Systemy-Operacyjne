from qtpy.QtCore import QThread

from gui.models.Algorithm import QAlgorithm

import copy
import logging
import operator
import collections


class FCFS(QAlgorithm):
    def __init__(self, que, start_pos, disk_size):
        super(FCFS, self).__init__()
        self.que = que
        self.start_pos = start_pos

    def run(self):
        logger = logging.getLogger("FCFS")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = self.start_pos
        time = incomming[0].arrive_time
        self.setHeadPos(current_pos)

        while True:
            QThread.msleep(100)
            for request in list(incomming):
                if request.arrive_time <= time:
                    incomming.remove(request)
                    queue.append(request)
                    self.addRequest(request.cylinder)

            if len(queue) != 0:
                request = queue.popleft()
                QThread.msleep(100)
                self.removeRequest(request.cylinder)

                # processes are sorted by arrive time so we do not have search for min
                # request: Request = min(queue, key=operator.attrgetter("arrive_time"))
                # queue.remove(request)
                completed.append(request)

                # calculate delta of head position and add it to time
                delta = abs(current_pos - request.cylinder)
                QThread.msleep(100)
                self.setHeadPos(current_pos)
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
