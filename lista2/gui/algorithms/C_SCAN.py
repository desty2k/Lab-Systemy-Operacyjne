from qtpy.QtCore import QThread

from gui.models.Request import Request
from gui.models.Algorithm import QAlgorithm

import copy
import logging
import operator
import collections


class C_SCAN(QAlgorithm):
    def __init__(self, que, start_pos, disk_size):
        super(C_SCAN, self).__init__()
        self.que = que
        self.start_pos = start_pos
        self.disk_size = disk_size

    def run(self):
        logger = logging.getLogger("C-SCAN")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = self.start_pos
        time = 0
        self.setHeadPos(current_pos)

        while True:
            for request in list(incomming):
                if request.arrive_time <= time:
                    queue.append(request)
                    incomming.remove(request)
                    self.addRequest(request.cylinder)

            for request_in_cylinder in [req for req in queue if req.cylinder == current_pos]:
                logger.debug("Request {} scaned on pos {}".format(request_in_cylinder.request_id,
                                                                  request_in_cylinder.cylinder))
                queue.remove(request_in_cylinder)
                completed.append(request_in_cylinder)
                QThread.msleep(100)
                self.removeRequest(request_in_cylinder.cylinder)

            time = time + 1
            if current_pos == self.disk_size:
                # time = time + current_pos
                current_pos = 0
            else:
                current_pos = current_pos + 1
            QThread.msleep(100)
            self.setHeadPos(current_pos)

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
