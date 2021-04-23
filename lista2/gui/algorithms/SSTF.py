from qtpy.QtCore import QThread

from gui.models.Request import Request
from gui.models.Algorithm import QAlgorithm

import copy
import logging
import operator
import collections


class SSTF(QAlgorithm):
    def __init__(self, que, start_pos, disk_size):
        super(SSTF, self).__init__()
        self.que = que
        self.start_pos = start_pos

    def run(self):
        logger = logging.getLogger("SSTF")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = self.start_pos
        time = incomming[0].arrive_time
        self.setHeadPos(current_pos)

        while True:
            for request in list(incomming):
                if request.arrive_time <= time:
                    queue.append(request)
                    incomming.remove(request)
                    self.addRequest(request.cylinder)

            if len(queue) != 0:
                nearest: Request = min(queue, key=lambda req: abs(current_pos - req.cylinder))
                queue.remove(nearest)
                completed.append(nearest)
                QThread.msleep(100)
                self.removeRequest(nearest.cylinder)

                # calculate delta of head position and add it to time
                delta = abs(current_pos - nearest.cylinder)
                current_pos = nearest.cylinder
                time = time + delta
                QThread.msleep(100)
                self.setHeadPos(current_pos)

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
