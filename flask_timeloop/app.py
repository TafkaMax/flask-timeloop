import logging
import sys
import signal
import time

from flask_timeloop.exceptions import ServiceExit
from flask_timeloop.job import Job
from flask_timeloop.helpers import service_shutdown


class _Timeloop():
    def __init__(self) -> None:
        # List of jobs, initalizied when app is run.
        self.jobs = {"to_run": [], "active": {}}
        # Run in a single thread.
        self.block = False
        # If start() is already initalized.
        self.already_started = False
        # Logger conf
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'))
        logger = logging.getLogger('timeloop')
        logger.addHandler(ch)
        logger.setLevel(logging.INFO)
        self.logger = logger
        

class Timeloop():
    def __init__(self, app=None):
        """Create Timeloop object that controls all timer jobs.
        
        Keyword Arguments:
            app: Flask application
        """
        if app is not None:
            self.state = self.init_app(app)
        else:
            self.state = None

    def init_timeloop(self, app):
        return _Timeloop()

    def init_app(self, app):
        """Initalizes timeloop from application settings.
        You can use this if you want to set up your Timeloop instance at configuration time.

        :param app: Flask application instance
        """
        state = self.init_timeloop(app)

        # register extension with app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['timeloop'] = state
        return state
    
    def __getattr__(self, name):
        return getattr(self.state, name, None)


    def job(self, interval = None, swarm = False, stop_on_exception = False, **kwargs):
        """Decorator useful to indicate a function that must looped call.
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
                _interval = _kwargs.pop("interval", interval) # override if interval is in kwargs
                self.add_job(f, _interval, stop_on_exception, *_args, **{**kwargs , **_kwargs})
                return f
                
            if swarm:
                return wrapper
            else:
                self.add_job(f, interval, stop_on_exception, **kwargs)
                return f
        return decorator

    def add_job(self, func, interval, exception, *args, **kwargs):
        """Create a new Job that executes in loop the func.
        
        Arguments:
            func {callable} -- The Job, object/function that must be call to
                execute the task.
            interval {timedelta} -- Time between two execution.
        
        Returns:
            int -- Identifier of job. If the job has be registered only, 
                identifier is None, it will be set during start of job.
        """
        if self.state:
            j = Job(interval, func, exception, self._logger, *args, **kwargs)
            self.state.logger.info("Registered job {}".format(j._execute))

            if self.state.already_started:
                self._start_job(j)
            else:
                self.state.jobs["to_run"].append(j)
            return j.ident
            
    def stop_all(self):
        """Stop all jobs
        """
        if self.state:
            for j in self.state.jobs["active"].values():
                self._stop_job(j)
            self.state.jobs["active"].clear()
            self.state.logger.info("Timeloop exited.")

    def stop_job(self, ident):
        """Stop the jobs
        """
        if self.state:
            j = self.state.jobs["active"].get(ident, None)
            if j: 
                self._stop_job(j)
                del self.state.jobs["active"][j.ident]

    def _stop_job(self, j):
        """Stop the jobs
        """
        if self.state:
            self.state.logger.info("Stopping job {}, that run {}".format(j.ident, j._execute))
            j.stop()

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
        if self.state:
            self.state.logger.info("Starting Timeloop..")
            self.state.block = block
            Job.stop_on_exception = stop_on_exception
            self._start_all(stop_on_exception = stop_on_exception)
            print(self._jobs)

            self.state.logger.info("Timeloop now started. Jobs will run based on the interval set")
            if block:
                self._block_main_thread()

    def _start_all(self, stop_on_exception):
        """Start all jobs create previusly by decorator. Set for every single job
        the block value and if must be stop on exception.
        
        Arguments:
            stop_on_exception {Exception of bool} -- Stop the looping of task if
                the Exception type is raised form task, if is bool True mean that
                the task will stop if occurs any type of Exception, False mean
                keep loop even if an exception is raised. This affect all job 
                will create except for jobs where the exception param is valued 
                (not False). (default: False)
        """
        if self.state:
            self.state.already_started = True
            for j in self.state.jobs["to_run"]:
                self._start_job(j)

    def _start_job(self, j):
        """Start thread of job.
        """
        if self.state:
            j.daemon = not self._block
            j.start()
            self.state.jobs["active"].update({j.ident:j})
            self.state.logger.info("Actived job {}".format(j._execute))

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

    def active_job(self, filter_function = lambda x: True):
        """Get info af all active job that match a filter.
        
        Arguments:
            filter {callable} -- a callable object that take dict arg and return
                True or False. Dict arg hava all info of job, use this if for 
                filtering. (default: lambda x: True)
        
        Returns:
            list -- list of all info of job that match a filter function
        """        
        res = []
        if self.state:
            for j in self.state.jobs["active"].values():
                info_j = j.get_info()
                if filter_function(info_j): 
                    res.append(info_j)
            return res
