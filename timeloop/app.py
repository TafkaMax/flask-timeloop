import logging
import sys
import signal
import time

from timeloop.exceptions import ServiceExit
from timeloop.job import Job
from timeloop.helpers import service_shutdown


class Timeloop():
    def __init__(self):
        self.jobs = []
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'))
        logger = logging.getLogger('timeloop')
        logger.addHandler(ch)
        logger.setLevel(logging.INFO)
        self.logger = logger

    def _add_job(self, func, interval, *args, **kwargs):
        """Create a new Job that execute in loop the func.
        
        Arguments:
            func {callable} -- The Job, object/function that must be call to
                execute the task.
            interval {timedelta} -- Time between two execution.
        """
        j = Job(interval, func, *args, **kwargs)
        self.jobs.append(j)

    def _block_main_thread(self):
        signal.signal(signal.SIGTERM, service_shutdown)
        signal.signal(signal.SIGINT, service_shutdown)

        while True:
            try:
                time.sleep(1)
            except ServiceExit:
                self.stop()
                break

    def _start_jobs(self, block, stop_on_exception):
        """Start all jobs create previusly by decorator. Set for every single job
        the block value and if must be stop on exception.
        
        Arguments:
            block {[type]} -- [description]
            stop_on_exception {bool} -- if the job must be stopped if it caught
                an exception; True is stopped, False continue a exection loop.
        """
        for j in self.jobs:
            j.daemon = not block
            j.stop_on_exception = stop_on_exception
            j.start()
            self.logger.info("Registered job {}".format(j._execute))

    def _stop_jobs(self):
        """Stop all jobs
        """
        for j in self.jobs:
            self.logger.info("Stopping job {}".format(j._execute))
            j.stop()

    def job(self, interval, swarm = False):
        """Decorator usefull to indicate a function that must looped call.
        If swarm is true allows to create a swarm of the same jobs with 
        different input parameters.

        Example:
            @timeloop.job(interval=1, swarm = True)
            def sample_job_every_2s(c):
                print("2s job current time : {}".format(c))

            for i in range(2):
                sample_job_every_1s(c = i)
        
        Arguments:
            interval {timedelta} -- Time between two execution.
        
        Raises:
            AttributeError: Interval must be timedelta or Number(int or float)
                if it is wrong type this exception is raised.
        """
        
        def decorator(f):
            def wrapper(*args, **kwargs):
                self._add_job(f, interval, *args, **kwargs)
                return f
                
            if swarm:
                return wrapper
            else:
                self._add_job(f, interval)
                return f
        return decorator

    def stop(self):
        """Stop all jobs
        """
        self._stop_jobs()
        self.logger.info("Timeloop exited.")

    def start(self, block = False, stop_on_exception = False):
        """Start all jobs create previusly by decorator.
        
        Keyword Arguments:
            block {bool} -- [description] (default: False)
            stop_on_exception {bool} -- if the job must be stopped if it caught
                an exception; True is stopped, False continue a exection loop.
                (default: False)
        """
        self.logger.info("Starting Timeloop..")
        self._start_jobs(block = block, stop_on_exception = stop_on_exception)

        self.logger.info("Timeloop now started. Jobs will run based on the interval set")
        if block:
            self._block_main_thread()
