from threading import Thread, Event
from datetime import timedelta
from time import time

class Job(Thread):
    def __init__(self, interval, execute, *args, **kwargs):
        """Simplest Job Thread that executes a task in loop. The time between two 
        execution is indicated by interval. All other arguments are arguments
        that must be sent to the executed function.
        
        Arguments:
            interval {timedelta} -- Time between two execution.
            execute {callable} -- The Job, object/function that must be call to
                execute the task.
        """        
        Thread.__init__(self)
        self.stopped = Event()
        self.interval = interval
        self.execute = execute
        self.args = args
        self.kwargs = kwargs
        self.stop_on_exception = False

    def stop(self):
        """Stop the job
        """        
        self.stopped.set()
        self.join()

    def run(self):
        """Start the loop of execution of the task. During loop is already take 
        into account the drift of time caused by the execution of the task. The
        loop is interrupted if stop_on_exception is True.
        """ 
        next_period = self.interval.total_seconds()
        next_time = time()
        
        while not self.stopped.wait(next_period):
            try:
                self.execute(*self.args, **self.kwargs)
            except:
                if self.stop_on_exception:
                    break
            next_time += self.interval.total_seconds()
            next_period = next_time - time()
