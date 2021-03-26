class Process:
    def __init__(self, process_id, arrive_time, duration):
        super(Process, self).__init__()

        self.id = process_id
        self.arrive_time = arrive_time
        self.duration = duration
        self.time_left = duration
        self.time_waiting = 0

    def set_time_left(self, t):
        self.time_left = t

    def set_wait_time(self, time):
        self.time_waiting = time

