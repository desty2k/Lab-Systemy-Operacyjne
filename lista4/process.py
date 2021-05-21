import typing
import collections

from request import Request


class Process:
    def __init__(self, que: list, page_count: int, thrashing_min_length, thrashing_factor):
        super(Process, self).__init__()
        self.time = 0
        self.running = True
        self.finished = False
        self.page_faults = 0
        self.page_count = page_count

        self.thrashing_step_count = 0
        self.thrashing_page_faults = 0
        self.thrashing_factor = thrashing_factor
        self.thrashing_min_length = thrashing_min_length
        self.thrashing = 0

        self.ppf = []
        self.wss = []

        self.incomming = collections.deque(que)
        self.completed = collections.deque()
        self.frames: typing.List[Request] = []

    def is_running(self):
        return self.running

    def set_running(self, value):
        self.running = value

    def is_finished(self):
        return self.finished

    def set_finished(self, value: bool):
        self.finished = value

    def set_frames_count(self, count):
        self.frames = [None] * count  # noqa

    def remove_frame(self):
        del self.frames[-1]

    def add_frame(self):
        self.frames.append(None)

    def frames_count(self):
        return len(self.frames)

    def get_page_count(self):
        return self.page_count

    def get_thrashing(self):
        return self.thrashing

    def get_ppf(self):
        return self.ppf

    def has_empty_frame(self):
        return any(page is None for page in self.frames)

    def has_frames(self):
        return len(self.frames) > 0

    def get_wss(self):
        return self.wss

    def get_time(self):
        return self.time

    def step(self):
        self.time += 1
        request: Request = self.incomming.popleft()
        if request.get_page() not in [req.get_page() for req in self.frames if req is not None]:
            self.page_faults += 1
            self.thrashing_page_faults += 1
            self.wss.append(request)
            self.ppf.append(request)
            if any(req is None for req in self.frames):
                self.frames[self.frames.index(None)] = request
            else:
                lru = min(self.frames, key=lambda f: f.get_last_used_time())
                self.frames[self.frames.index(lru)] = request
        else:
            for frame in self.frames:
                if frame and frame.get_page() == request.get_page():
                    frame.set_last_used_time(request.get_last_used_time())

        self.thrashing_step_count += 1
        if self.thrashing_step_count >= self.thrashing_min_length:
            if self.thrashing_page_faults / self.thrashing_step_count >= self.thrashing_factor:
                self.thrashing += 1
            self.thrashing_step_count = 0
            self.thrashing_page_faults = 0

        self.completed.append(request)
        if len(self.incomming) == 0:
            self.set_finished(True)
