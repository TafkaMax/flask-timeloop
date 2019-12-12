from threading import Thread, Event
from datetime import timedelta
from time import time

import traceback

class Job(Thread):

    general_exception = False
    
    def __init__(self, interval, execute, exception = False, *args, **kwargs): 
        """Simplest Job Thread that executes a task in loop. The time between two 
        execution is indicated by interval. Exception param stop the looping of 
        task if the exception type is raised form task, if is bool True mean that 
        the task will stop if occurs any type of Exception, False mean still loop
        even if an exception is raised. If exception is False the job see the 
        general_exception attribute that follow the same rule of exception param
        but is for all job that not have specification. All other arguments are 
        arguments that must be sent to the executed function.
        
        Arguments:
            interval {timedelta or float} -- Time between two execution if it's a 
                floating point number specifying a time in seconds (or fractions
                thereof).
            execute {callable} -- The Job, object/function that must be call to
                execute the task.
            exception {Exception of bool} -- Stop the looping of task if the
                Exception type is raised form task, if is bool True mean that the
                task will stop if occurs any type of Exception, False mean keep
                loop even if an exception is raised (default: False)
        Raises:
            AttributeError: If Interval is wrong type, if exception is wrong type
        """        
        Thread.__init__(self)
        self.stopped = Event()
        
        # Check interval param
        if isinstance(interval,timedelta):
            self._interval = interval.total_seconds()
        elif isinstance(interval, (int, float)):
            self._interval = interval
        else:
            raise AttributeError("Interval must be timedelta or number of \
                seconds(or fractions thereof).")

        # Check exception param and if False see general_exception
        if isinstance(exception, bool):
            if exception:
                self._exception = Exception
            else:
                if isinstance(Job.general_exception, bool):
                    if Job.general_exception:
                        self._exception = Exception
                    else:
                        self._exception = False
                elif issubclass(Job.general_exception, Exception):
                    self._exception = Job.general_exception
                else:
                    raise AttributeError("exception must be a subclass on Exception or Bool.")
        elif issubclass(exception, Exception):
            self._exception = exception
        else:
            raise AttributeError("exception must be a subclass on Exception or Bool.")

        self._execute = execute
        self._args = args
        self._kwargs = kwargs

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
            except Exception as e:
                traceback.print_exc()
                if self._exception != False and isinstance(e, self._exception):
                    break
            next_time += self._interval
            next_period = next_time - time()
