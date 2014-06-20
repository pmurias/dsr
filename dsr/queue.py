class Job:
    def __init__(self,time,cb):
        self.time = time
        self.cb = cb
class Queue:
    def __init__(self):
       self.jobs = []
    def ready(self,time):
        for job in self.jobs:
            if job.time <= time:
                return job
    def execute(self,time):
        while self.ready(time) is not None:
            ready = self.ready(time)
            self.jobs.remove(ready)
            ready.cb()
    def add(self,time,cb):
        self.jobs.append(Job(time,cb))
