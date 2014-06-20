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
        execute = []
        keep = []

        for job in self.jobs:
            if job.time <= time:
                execute.append(job)
            else:
                keep.append(job)

        self.jobs = keep

        for job in execute:
            job.cb()
    def add(self,time,cb):
        self.jobs.append(Job(time,cb))
