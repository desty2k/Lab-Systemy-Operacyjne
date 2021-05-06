

class Request:

    def __init__(self, page, arrive_time, local=False):
        super(Request, self).__init__()
        self.page = page
        self.arrive_time = arrive_time
        self.last_used_time = arrive_time
        self.recall_byte = 1
        self.local = local

    def is_local(self):
        return self.local

    def get_recall_byte(self):
        return self.recall_byte

    def set_recall_byte(self, value):
        self.recall_byte = value

    def get_page(self):
        return self.page

    def get_arrive_time(self):
        return self.arrive_time

    def get_last_used_time(self):
        return self.last_used_time

    def set_last_used_time(self, time):
        self.last_used_time = time

    def __str__(self):
        return "Request-{}-{}::Local-{}".format(self.arrive_time, self.page, self.local)
