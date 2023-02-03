from datetime import timedelta
import logging
import sys
import signal
import time

from flask_timeloop.exceptions import ServiceExit
from flask_timeloop.job import Job
from flask_timeloop.helpers import service_shutdown


class _Timeloop():
    def __init__(self, app) -> None:
        # List of jobs, initalizied when app is run.
        self.jobs = {"to_run": [], "active": {}}
        # Run in a single thread.
        self.block = False
        # If start() is already initalized.
        self.already_started = False
        # Logger conf
        timeloop_handler = logging.StreamHandler(sys.stdout)
        timeloop_handler.setLevel(logging.INFO)
        timeloop_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'))
        app.logger.addHandler(timeloop_handler)
        # Add application as an object for timeloop.
        self.app = app
        

class Timeloop():
    def __init__(self, app=None):
        """Create a Timeloop object that controls all timer jobs.
        
        Keyword Arguments:
            app: Flask application
        """
        if app is not None:
            self.state = self.init_app(app)
        else:
            self.state = None

    def init_timeloop(self, app):
        return _Timeloop(app)

    def init_app(self, app):
        """Initalizes timeloop object from application settings.
        You can use this if you want to set up your Timeloop instance at configuration time.

        :param app: Flask application instance
        """
        # Initalize state from Flask app
        state = self.init_timeloop(app)
        # Set the state of the application for the current Timeloop object.
        self.state = state

        # register extension with Flask app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['timeloop'] = state
        return state
    
    def __getattr__(self, name):
        return getattr(self.state, name, None)


    def job(self, interval: timedelta, swarm = False, stop_on_exception = False, **kwargs):
        """Decorator useful to indicate a function that must be looped.
        If swarm is true allows to create a swarm of the same jobs with 
        different input parameters.

        Example:
            @timeloop.job(interval=1, swarm = True)
            def sample_job_every_2s(c):
                print("2s job current time : {}".format(c))

            for i in range(2):
                sample_job_every_1s(c = i)
        
        Arguments:
            interval {timedelta} -- Time between two executions.
            swarm {bool} -- If True, allows to declare a job calling a function 
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
                _interval = _kwargs.pop("interval", interval) # override if interval is in kwargs
                self.add_job(f, _interval, stop_on_exception, *_args, **{**kwargs , **_kwargs})
                return f
                
            if swarm:
                return wrapper
            else:
                self.add_job(f, interval, stop_on_exception, **kwargs)
                return f
        return decorator

    def add_job(self, func, interval: timedelta, exception: bool, *args, **kwargs):
        """Create a new Job that executes in a loop, the function.
        
        Arguments:
            func {callable} -- The Job, object/function that must be called to
                execute the task.
            interval {timedelta} -- Time between two executions.
        
        Returns:
            int -- Identifier of job. If the job has to be registered only, 
                identifier is None, it will be set during start of job.
        """
        if self.state:
            job = Job(interval, func, exception, logger=self.state.app.logger, *args, **kwargs)
            self.state.app.logger.info("Registered job: {}".format(job._execute))

            # Timeloop .start() has been called, then start the job.
            if self.state.already_started:
                self._start_job(job)
            else:
                self.state.jobs["to_run"].append(job)
            return job.ident
            
    def stop_all(self):
        """Stop all jobs
        """
        if self.state:
            # Loop over active 'Job' values and stop them.
            for job in self.state.jobs["active"].values():
                self._stop_job(job)
            # Clear active jobs dictionary.
            self.state.jobs["active"].clear()
            self.state.app.logger.info("Timeloop exited.")

    def stop_job(self, ident):
        """Stop the jobs
        """
        if self.state:
            job = self.state.jobs["active"].get(ident, None)
            if job: 
                self._stop_job(job)
                del self.state.jobs["active"][job.ident]

    def _stop_job(self, job: Job):
        """Stop the jobs
        """
        if self.state:
            self.state.app.logger.info("Stopping job {}, that is running {}".format(job.ident, job._execute))
            job.stop()

    def start(self, block: bool = False, stop_on_exception: bool = False):
        """Start all jobs previously created by a decorator.
        
        Keyword Arguments:
            block {bool} -- block Main thread, if set to True. (default: False)
            stop_on_exception {Exception of bool} -- Stop the looping of a task if
                the Exception type is raised form task. True measn that
                the task will stop if any type of Exception occurs, False means
                that the function will keep looping, even if an exception occurs. (default: False)
        """
        # Only start the the timeloop, if state exists. State is initalized, when Flask app is added as an parameter to init_app or during __init__.
        if self.state:
            self.state.app.logger.info("Starting Timeloop..")
            # Initalize block
            self.state.block = block
            # TODO check, maybe the next one can be done better.
            #Job.stop_on_exception = stop_on_exception
            self._start_all(stop_on_exception = stop_on_exception)

            self.state.app.logger.info("Timeloop service now started. Jobs will run based on a set interval.")
            # If block is set, block main thread.
            if block:
                self._block_main_thread()

    def _start_all(self, stop_on_exception: bool):
        """Start all jobs previusly created by a decorator. Set for every single job
        the block main thread value and if must be stopped on exception.
        
        Arguments:
            stop_on_exception {Exception or bool} -- Stop the looping of task if
                the Exception type is raised form task, if is True it means that
                the task will stop if any type of Exception occurs, False means
                that it will keep looping even if an exception is raised.
                (not False). (default: False)
        """
        if self.state:
            self.state.already_started = True
            for job in self.state.jobs["to_run"]:
                self._start_job(job)

    def _start_job(self, job: Job):
        """Start job in a thread.
        """
        # If state is not None
        if self.state:
            job.daemon = not self._block
            # Start the job.
            job.start()
            # Set the job as an 'active' job
            self.state.jobs["active"].update({job.ident:job})
            self.state.app.logger.info("Activated job: {}".format(job._execute))

    def _block_main_thread(self):
        """Block the main thread if block param in start function is True.
        """        
        signal.signal(signal.SIGTERM, service_shutdown)
        signal.signal(signal.SIGINT, service_shutdown)

        while True:
            try:
                time.sleep(1)
            except ServiceExit:
                self.stop_all()
                break

    #TODO currently not in use, find out what to do with this method.
    def active_job(self, filter_function = lambda x: True):
        """Get info of all active jobs that match a filter.
        
        Arguments:
            filter {callable} -- a callable object that take dict arg and return
                True or False. Dict arg hava all info of job, use this if for 
                filtering. (default: lambda x: True)
        
        Returns:
            list -- list of all info of job that match a filter function
        """        
        result = []
        if self.state:
            for job in self.state.jobs["active"].values():
                job_info = job.get_info()
                if filter_function(job_info): 
                    result.append(job_info)
            return result
