import copy
import pickle
import random
import logging

from utils import Logger
from process import Process
from request import Request

LOGGING_LEVEL = logging.DEBUG
PICKLED_FILENAME = "processes.dump"

PROCESS_COUNT = 10

# min and max amount of used pages
MIN_PAGE_COUNT = 10
MAX_PAGE_COUNT = 30

THRASHING_MIN_LENGTH = 10
THRASHING_FACTOR = 0.5

REQUESTS_COUNT = 5000
FRAMES_COUNT = 40
LOCAL_REQUESTS_MIN_LENGTH = 1
LOCAL_REQUESTS_MAX_LENGTH = 15
LOCAL_REQUESTS_MAX_DELTA = 2
LOCAL_REQUESTS_CHANCE = 3  # range 1-10 | *10% chance of generating local requests sequence

PPF_LOW = 0.2
PPF_HIGH = 0.8
PPF_TIME_WINDOW = 10

WSS_TIME_WINDOW = 5
WSS_C = 4


class Main:

    def __init__(self):
        super(Main, self).__init__()
        self.processes: list[Process] = []

        self.logger = logging.getLogger()
        self.logger.info("Frames count is {}".format(FRAMES_COUNT))
        self.logger.info("Thrashing factor is {}".format(THRASHING_FACTOR))

    def create_requests(self, process_size) -> list:
        """Fills queue with page access requests."""
        que = []
        arrive_time = 1
        while arrive_time != REQUESTS_COUNT + 1:
            if random.randint(0, 10) < LOCAL_REQUESTS_CHANCE:
                # generate sequence of local request
                local_length = random.randint(LOCAL_REQUESTS_MIN_LENGTH, LOCAL_REQUESTS_MAX_LENGTH)
                local_mid_page = random.randint(1, process_size + 1)
                for i in range(local_length):
                    if arrive_time >= REQUESTS_COUNT + 1:
                        break
                    while True:
                        # generate random page and check if it exists in memory
                        local_page = local_mid_page + random.randint(-LOCAL_REQUESTS_MAX_DELTA,
                                                                     LOCAL_REQUESTS_MAX_DELTA)
                        if local_page in range(1, process_size + 1):
                            break
                    que.append(Request(local_page, arrive_time, local=True))
                    arrive_time = arrive_time + 1

            else:
                # generate one random request
                que.append(Request(random.randint(1, process_size + 1), arrive_time))
                arrive_time = arrive_time + 1
        return que

    def create_processes(self):
        """Create x processes with random size."""
        for _ in range(PROCESS_COUNT):
            proc_size = random.randint(MIN_PAGE_COUNT, MAX_PAGE_COUNT)
            self.processes.append(Process(self.create_requests(proc_size), proc_size,
                                          THRASHING_MIN_LENGTH, THRASHING_FACTOR))

    def save_processes_to_file(self) -> None:
        """Saves requests to file using pickle."""
        with open(PICKLED_FILENAME, "wb") as file:
            pickle.dump(self.processes, file)

    def load_processes_from_file(self) -> None:
        """Load requests from files using pickle."""
        with open(PICKLED_FILENAME, "rb") as file:
            self.processes = pickle.load(file)

    def run_equal_allocation(self):
        logger = logging.getLogger("EQUAL_ALLOCATION")
        processes = copy.deepcopy(self.processes)

        for proc in processes:
            proc.set_frames_count(int(FRAMES_COUNT / proc.get_page_count()))
        while any(not process.is_finished() for process in processes):
            for proc in processes:
                proc.step()

        logger.info("================= EQUAL_ALLOCATION =================")
        logger.info(
            "Average page faults {}".format(int(sum(proc.page_faults for proc in processes) / len(self.processes))))
        logger.info(
            "Average thrashing {}".format(int(sum(proc.get_thrashing() for proc in processes)) / len(self.processes)))

    def run_proportional_allocation(self):
        logger = logging.getLogger("PROPORTIONAL_ALLOCATION")
        processes = copy.deepcopy(self.processes)
        pages_sum = sum(proc.get_page_count() for proc in processes)

        for proc in processes:
            proc.set_frames_count(int(proc.get_page_count() * FRAMES_COUNT / pages_sum))
        while any(not process.is_finished() for process in processes):
            for proc in processes:
                proc.step()

        logger.info("================= PROPORTIONAL_ALLOCATION =================")
        logger.info(
            "Average page faults {}".format(int(sum(proc.page_faults for proc in processes) / len(self.processes))))
        logger.info(
            "Average thrashing {}".format(int(sum(proc.get_thrashing() for proc in processes)) / len(self.processes)))

    def run_dynamic_fault_frequency(self):
        logger = logging.getLogger("FAULT_FREQUENCY_CONTROL")
        processes = copy.deepcopy(self.processes)
        finished = []
        pages_sum = sum(proc.get_page_count() for proc in processes)
        free_frames = FRAMES_COUNT
        time = 0

        logger.info("================= FAULT FREQUENCY CONTROL =================")
        logger.info("Fault frequency control works better if the page draw range is high")

        for proc in processes:
            frames = int(proc.get_page_count() * FRAMES_COUNT / pages_sum)
            free_frames -= frames
            proc.set_frames_count(frames)
            if not proc.has_frames():
                proc.set_running(False)

        while any(not process.is_finished() for process in processes):
            time += 1
            for proc in processes:
                if not proc.is_finished():
                    if proc.is_running():
                        proc.step()
                        for req in proc.get_ppf():
                            if req.get_arrive_time() + PPF_TIME_WINDOW < proc.get_time():
                                proc.ppf.remove(req)

                        if len(proc.get_ppf()) > 0 and proc.get_time() > PPF_TIME_WINDOW:
                            ppf = len(proc.get_ppf()) / PPF_TIME_WINDOW
                            if ppf <= PPF_LOW:
                                proc.remove_frame()
                                free_frames += 1
                                if not proc.has_frames():
                                    proc.set_running(False)
                            elif ppf >= PPF_HIGH:
                                if free_frames > 0:
                                    proc.add_frame()
                                    free_frames -= 1
                    else:
                        if free_frames > 0:
                            proc.set_running(True)
                            while free_frames > 0:
                                proc.add_frame()
                                free_frames -= 1
                            proc.step()
                else:
                    while proc.has_frames():
                        proc.remove_frame()
                        free_frames += 1
                    processes.remove(proc)
                    finished.append(proc)

        logger.info(
            "Average page faults {}".format(int(sum(proc.page_faults for proc in finished) / len(self.processes))))
        logger.info(
            "Average thrashing {}".format(int(sum(proc.get_thrashing() for proc in finished)) / len(self.processes)))

    def run_dynamic_zone(self):
        logger = logging.getLogger("ZONE_MODEL")
        processes = copy.deepcopy(self.processes)
        finished = []
        pages_sum = sum(proc.get_page_count() for proc in processes)
        free_frames = FRAMES_COUNT
        time = 0

        logger.info("================= ZONE MODEL =================")
        logger.info("Zone model works better for a large number of local requests")

        for proc in processes:
            frames = int(proc.get_page_count() * FRAMES_COUNT / pages_sum)
            free_frames -= frames
            proc.set_frames_count(frames)
            if not proc.has_frames():
                proc.set_running(False)

        while any(not process.is_finished() for process in processes):
            time += 1

            if len(processes) == 1:
                while free_frames > 0:
                    processes[0].add_frame()
                    free_frames -= 1
                processes[0].set_running(True)

            else:
                # process wss
                if time > WSS_TIME_WINDOW and time % WSS_C == 0:
                    running = [proc for proc in processes if proc.is_running()]
                    d = sum(len(proc.get_wss()) for proc in running)
                    if d <= FRAMES_COUNT:
                        free_frames = FRAMES_COUNT
                        for proc in running:
                            len_wss = len(proc.get_wss())
                            if len_wss > 0:
                                if free_frames > 0:
                                    min_wss = min([len_wss, free_frames])
                                    free_frames -= min_wss
                                    while proc.frames_count() != min_wss:
                                        if proc.frames_count() > min_wss:
                                            proc.remove_frame()
                                        elif proc.frames_count() < min_wss:
                                            proc.add_frame()
                                else:
                                    proc.set_running(False)
                            else:
                                free_frames -= proc.frames_count()

                    else:
                        lowest_wss = min(processes, key=lambda proc: len(proc.get_wss()))
                        lowest_wss.set_running(False)
                        while lowest_wss.has_frames():
                            lowest_wss.remove_frame()
                            free_frames += 1

                        free_frames = FRAMES_COUNT
                        for proc in processes:
                            if proc is not lowest_wss:
                                proc.set_running(True)
                                frames = int(proc.get_page_count() * FRAMES_COUNT /
                                             sum(proc.get_page_count() for proc in processes if proc is not lowest_wss))
                                while proc.frames_count() != frames:
                                    if proc.frames_count() > frames:
                                        proc.remove_frame()
                                    elif proc.frames_count() < frames:
                                        proc.add_frame()
                                free_frames -= frames
                                if proc.frames_count() == 0:
                                    proc.set_running(False)

            for proc in processes:
                if not proc.is_finished():
                    if proc.is_running():
                        proc.step()
                        for req in proc.get_wss():
                            if req.get_arrive_time() + WSS_TIME_WINDOW < proc.get_time():
                                proc.wss.remove(req)
                else:
                    while proc.has_frames():
                        proc.remove_frame()
                        free_frames += 1
                    processes.remove(proc)
                    finished.append(proc)

        logger.info(
            "Average page faults {}".format(int(sum(proc.page_faults for proc in finished) / len(self.processes))))
        logger.info(
            "Average thrashing {}".format(int(sum(proc.get_thrashing() for proc in finished)) / len(self.processes)))


if __name__ == '__main__':
    log = Logger()
    log.enable()
    log.set_level(LOGGING_LEVEL)

    m = Main()
    m.create_processes()
    m.save_processes_to_file()
    # m.load_processes_from_file()
    m.run_equal_allocation()
    m.run_proportional_allocation()
    m.run_dynamic_fault_frequency()
    m.run_dynamic_zone()
