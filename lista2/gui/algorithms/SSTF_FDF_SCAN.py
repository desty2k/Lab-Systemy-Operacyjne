from qtpy.QtCore import QThread

from gui.models.Request import Request
from gui.models.Algorithm import QAlgorithm

import copy
import logging
import operator
import collections


class SSTF_FDF_SCAN(QAlgorithm):
    def __init__(self, que, start_pos, disk_size):
        super(SSTF_FDF_SCAN, self).__init__()
        self.que = que
        self.start_pos = start_pos
        self.disk_size = disk_size

    def run(self):
        logger = logging.getLogger("SSTF-FDF-SCAN")
        incomming = collections.deque(copy.deepcopy(self.que))
        queue = collections.deque()
        completed = collections.deque()
        current_pos = self.start_pos
        time = incomming[0].arrive_time
        target = None
        self.setHeadPos(current_pos)

        while True:
            for request in list(incomming):
                if request.arrive_time <= time:
                    queue.append(request)
                    incomming.remove(request)
                    self.addRequest(request.cylinder)

            logger.debug("POS: {} QUEUE: {}".format(current_pos, [str(req.cylinder) + "*" if req.real_time
                                                                  else str(req.cylinder) for req in queue]))
            if len(queue) != 0:
                if target:
                    if target.cylinder == current_pos:
                        logger.debug("Head over target cylinder {}".format(current_pos))
                        queue.remove(target)
                        completed.append(target)
                        QThread.msleep(100)
                        self.removeRequest(target.cylinder)
                        target = None
                    else:
                        for request_in_cylinder in [req for req in queue if req.cylinder == current_pos]:
                            logger.debug("Request {} scaned on pos {}".format(request_in_cylinder.request_id,
                                                                              request_in_cylinder.cylinder))
                            queue.remove(request_in_cylinder)
                            completed.append(request_in_cylinder)
                            self.removeRequest(request_in_cylinder.cylinder)

                        time = time + 1
                        if current_pos < target.cylinder:
                            current_pos = current_pos + 1
                        else:
                            current_pos = current_pos - 1
                        time = time + 1
                        for other in list(queue):
                            other.add_wait_time(1)

                        QThread.msleep(100)
                        self.setHeadPos(current_pos)

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
                            self.removeRequest(nearest.cylinder)

                            # calculate delta of head position and add it to time
                            delta = abs(current_pos - nearest.cylinder)
                            current_pos = nearest.cylinder
                            time = time + delta

                            for other in list(queue):
                                other.add_wait_time(delta)

                            QThread.msleep(100)
                            self.setHeadPos(current_pos)
                    else:
                        # no real time requests, fallback to sstf
                        nearest: Request = min(queue, key=lambda req: abs(current_pos - req.cylinder))
                        queue.remove(nearest)
                        completed.append(nearest)
                        self.removeRequest(nearest.cylinder)

                        # calculate delta of head position and add it to time
                        delta = abs(current_pos - nearest.cylinder)
                        current_pos = nearest.cylinder
                        time = time + delta

                        for other in list(queue):
                            other.add_wait_time(delta)

                        QThread.msleep(100)
                        self.setHeadPos(current_pos)

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
