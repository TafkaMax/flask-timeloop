from threading import Thread, Event
from datetime import timedelta
from time import time

class Job(Thread):
    def __init__(self, interval, execute, *args, **kwargs):
        """Simplest Job Thread that executes a task in loop. The time between two 
        execution is indicated by interval. All other arguments are arguments
        that must be sent to the executed function.
        
        Arguments:
            interval {timedelta or float} -- Time between two execution if it's a 
                floating point number specifying a time in seconds (or fractions
                thereof).
            execute {callable} -- The Job, object/function that must be call to
                execute the task.
        Raises:
            AttributeError: If Interval is wrong type
        """        
        Thread.__init__(self)
        self.stopped = Event()
        
        if isinstance(interval,timedelta):
            self._interval = interval.total_seconds()
        elif isinstance(interval, (int, float)):
            self._interval = interval
        else:
            raise AttributeError("Interval must be timedelta or number of \
                seconds(or fractions thereof).")
        
        self._execute = execute
        self._args = args
        self._kwargs = kwargs
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
        next_period = self._interval
        next_time = time()

        while not self.stopped.wait(next_period):
            try:
                self._execute(*self._args, **self._kwargs)
            except:
                if self.stop_on_exception:
                    break
            next_time += self._interval
            next_period = next_time - time()
