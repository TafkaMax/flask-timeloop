import logging
import sys
import signal
import time

from timeloop.exceptions import ServiceExit
from timeloop.job import Job
from timeloop.helpers import service_shutdown


class Timeloop():
    def __init__(self, logger = None):
        """Create Timeloop object that control all job.
        
        Keyword Arguments:
            logger {logging} -- If you have already a logger you can set with 
                this the logger of Timeloop. (default: {None})
        """
        self._jobs = []
        if not logger:
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            ch.setFormatter(logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'))
            logger = logging.getLogger('timeloop')
            logger.addHandler(ch)
            logger.setLevel(logging.INFO)
        self.logger = logger

    def _add_job(self, func, interval, exception, *args, **kwargs):
        """Create a new Job that execute in loop the func.
        
        Arguments:
            func {callable} -- The Job, object/function that must be call to
                execute the task.
            interval {timedelta} -- Time between two execution.
        """
        j = Job(interval, func, exception, *args, **kwargs)
        self._jobs.append(j)

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
            stop_on_exception {Exception of bool} -- Stop the looping of task if
                the Exception type is raised form task, if is bool True mean that
                the task will stop if occurs any type of Exception, False mean
                keep loop even if an exception is raised. This affect all job 
                will create except for jobs where the exception param is valued 
                (not False). (default: False)
        """
        for j in self._jobs:
            j.daemon = not block
            j.start()
            self.logger.info("Registered job {}".format(j._execute))

    def _stop_jobs(self):
        """Stop all jobs
        """
        for j in self._jobs:
            self.logger.info("Stopping job {}".format(j._execute))
            j.stop()

    def job(self, interval, swarm = False, stop_on_exception = False, **kwargs):
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
            swarm {bool} -- If True allows to declare a job calling a function 
                where is posted a decorator. The advantage is that you can 
                specify a value of param of the task; See example.
            exception {Exception of bool} -- Stop the looping of task if the
                Exception type is raised form task, if is bool True mean that the
                task will stop if occurs any type of Exception, False mean keep
                loop even if an exception is raised (default: False)
        
        Raises:
            AttributeError: Interval must be timedelta or Number(int or float)
                if it is wrong type this exception is raised.
        """
        
        def decorator(f):
            def wrapper(*_args, **_kwargs):
                self._add_job(f, interval, stop_on_exception, *_args, **{**kwargs , **_kwargs})
                return f
                
            if swarm:
                return wrapper
            else:
                self._add_job(f, interval, stop_on_exception, **kwargs)
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
            stop_on_exception {Exception of bool} -- Stop the looping of task if
                the Exception type is raised form task, if is bool True mean that
                the task will stop if occurs any type of Exception, False mean
                keep loop even if an exception is raised. This affect all job 
                will create except for jobs where the exception param is valued 
                (not False). (default: False)
        """
        self.logger.info("Starting Timeloop..")
        Job.stop_on_exception = stop_on_exception
        self._start_jobs(block = block, stop_on_exception = stop_on_exception)

        self.logger.info("Timeloop now started. Jobs will run based on the interval set")
        if block:
            self._block_main_thread()
