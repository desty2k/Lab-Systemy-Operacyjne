

class Request:

    def __init__(self, arrive_time, cylinder, real_time=False, deadline=0):
        super(Request, self).__init__()
        self.wait_time = 0
        self.cylinder = cylinder

        self.request_id = 0
        self.arrive_time = arrive_time
        self.real_time = real_time
        self.deadline = deadline

    def add_wait_time(self, time: int):
        self.wait_time = self.wait_time + time

    def set_wait_time(self, time: int):
        self.wait_time = time

    def set_id(self, request_id: int):
        self.request_id = request_id
