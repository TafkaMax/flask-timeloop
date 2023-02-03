from threading import Thread, Event
from datetime import timedelta
from time import time

import logging
import sys

class Job(Thread):

    general_exception = False
    
    def __init__(self, interval: timedelta, execute, exception = False, logger = None,  *args, **kwargs): 
        """Simplest Job Thread that executes a task in a loop. The time between two 
        executions is indicated by an interval. Exception param stops the looping of 
        task if the exception type is raised form task, if the exception is a boolean with the value being True, then the task will stop if any type of Exception occurs. When exception boolean is set to False, then the loop will continue even if an exception is raised. 
        If exception is set to False, then look at 
        general_exception attribute that follows the same rule of exception param
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
            logger {logging} -- Log object where will print the Exception raised
                from the job. Uf None stdout will be set. (default: None)
        Raises:
            AttributeError: If Interval is wrong type, if exception is wrong type
        """
        Thread.__init__(self)
        self.stop_on_exception = None
        self.stopped = Event()
        if logger:
            self._logger = logger
        else:
            self._logger = logging.StreamHandler(sys.stdout)
        
        # Check interval param
        if isinstance(interval,timedelta):
            self._interval = interval.total_seconds()
        elif isinstance(interval, (int, float)):
            if interval <= 0:
                raise AttributeError("Interval when int must be greater than 0.")
            self._interval = interval
        elif interval == None:
            raise AttributeError("Interval must be set during declation of job.")
        else:
            raise AttributeError("Interval must be timedelta or number of seconds(or fractions thereof).")

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
                    raise AttributeError("exception must be a subclass of Exception or Bool.")
        elif isinstance(exception, type) and issubclass(exception, Exception):
            self._exception = exception
        else:
            raise AttributeError("exception must be a subclass of Exception or Bool.")

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
        loop is interrupted if stop_on_exception is True when a Exception is raise.
        """ 
        next_period = self._interval
        next_time = time()

        while not self.stopped.wait(next_period):
            try:
                self._execute(*self._args, **self._kwargs)
            except Exception as e:
                logging.exception(type(e).__name__ + " is raise from " + str(self._execute))
                if self._exception != False and isinstance(e, self._exception):
                    break
            next_time += self._interval
            next_period = next_time - time()

    def get_info(self):
        """Get all useful info of job in a dict.
            {ident": int,
            "interval": int(sec),
            "exception": Exception subclass,
            "execute": function,
            "args": tupla,
            "kwargs": dict}
        
        Returns:
            dict -- dict with all information.
        """        
        return {
            "ident": self.ident,
            "interval": self._interval,
            "exception": self._exception,
            "execute": self._execute,
            "args": self._args,
            "kwargs": self._kwargs}
