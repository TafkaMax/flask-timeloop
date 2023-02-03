# Flask-Timeloop
Timeloop is a service that can be used to run periodic tasks after a certain interval. It is **meant** to be used to with an underlying flask application.

Each job runs on a separate thread and when the service is shut down, it waits till all tasks currently being executed are completed.

Forked and enhanced from [`here`](https://github.com/sankalpjonn/timeloop.git)
Forked and enchanced from [`here`](https://github.com/Ruggiero-Santo/timeloop.git)

#### PyPi

https://pypi.org/project/flask-timeloop/

## Installation

### pip

```sh
pip install flask-timeloop
```

#### Clone and install
```sh
git clone https://github.com/TafkaMax/timeloop.git
sudo python setup.py install
```

#### Direct installation 
```sh
pip install git+https://github.com/TafkaMax/timeloop.git
```

#### Poetry
```sh
poetry add flask-timeloop
```

# Usage

The recommended way is to use this library with flask factory pattern.

**NB! This is not the correct way to implement the flask extension, as I add the application context to the extension data. BUT Flask only works during requests, but this functionality is internal and does not care about requests. It's like a cron, but inside the application.**

## Writing jobs

### Factory pattern

```python
#python_project_folder/your_app_name/extensions.py
from flask_timeloop import Timeloop

timeloop = Timeloop()
```

```python
#python_project_folder/your_app_name/__init__.py
#(this can also be main.py or whatever you want.)

from flask import Flask

def create_app():
    app = Flask(__name__)

    # Import timeloop and join timeloop to flask application
    from your_app_name.extensions import flask-timeloop
    timeloop.init_app(app)
    # Start the timeloop
    timeloop.start()
    return app
```

```python
#python_project_folder/main.py
from your_app_name import create_app
app = create_app()
```

```python
from your_app_name.extensions import timeloop

@timeloop.job(interval=timedelta(minutes=10))
def do_something():
    with timeloop.app.app_context():
        do_something_that_needs_application_context()
```

### Basic one file application.

```python
#main.py
import time

from timeloop import Timeloop
from datetime import timedelta

from flask import Flask


app = Flask(__name__)

tl = Timeloop(app)

@tl.job(interval = timedelta(seconds = 2))
def sample_job_every_2s():
    print( "2s job current time : {}".format(time.ctime()) )

@tl.job(interval = 5)
def sample_job_every_5s():
    print( "5s job current time : {}".format(time.ctime()) )


@tl.job(interval = timedelta(seconds = 10))
def sample_job_every_10s():
    print( "10s job current time : {}".format(time.ctime()) )
```

## Writing jobs with arguments
Allow to create a job with specified parameters in input
```python
class FileToMove:
    tl = Timeloop()

    def start(self):
        self.tl.start(True)

    # ATTENTION: If a job wants the self param must be declared as swarm.
    # This is because the instance isn't already created when the job is registered
    @tl.job(interval = 1, swarm = True, param_2 = "param")
    def timedMethod(self, param_1, param_2):
        print(self, "param_1:", param_1, "; param_2:", param_2)

    @tl.job(interval = 2, param_1 = "uno", param_2 = "param")
    def timedMethod_1(param_1, param_2):
        print("param_1:", param_1, "; param_2:", param_2)

    # produce the same effect of timedMethod_1. 
    @tl.job(interval = 3 )
    def timedMethod_2(param_1 = "uno", param_2 = "param"):
        print("param_1:", param_1, "; param_2:", param_2)

if __name__ == "__main__":
    ob1 = FileToMove()
    ob1.timedMethod("try")
    ob1.start()
```
or multiple jobs of the same function but with different parameters. It can be really useful in a situation like above when you want to call a class function.
```python
@tl.job(interval = timedelta(seconds = 5), swarm = True)
def sample_job(idx):
    print( "Task id: {} | time: {}".format(idx, time.ctime()) )

# example: queue jobs with different ids
for id in range(1, 3):
	sample_job(id)
```
In the job declared with  `swarm = True` the param `interval` can be omitted. This allows you to create a swarm of job with different interval, including `interval = 2` or `interval = timedelta(seconds = 2)` in the creation, like example.
```python
@tl.job(swarm = True)
def sample_job(idx):
    print( "Task id: {} | time: {}".format(idx, time.ctime()) )

# example: same jobs with different interval
for id in range(1, 3):
	sample_job(id, interval = id)
```

## Writing jobs that stop if an exception occurs
```python
@tl.job(interval = timedelta(seconds = 2), exception = True)
def sample_job():
    print( "I will die if any Exception occurs,time : {}".format(time.ctime()) )

@tl.job(interval = 2, exception = AttributeError)
def sample_job():
    print( "I will die soon, but only if AttributeError occurs" )
    raise AttributeError

@tl.job(interval = timedelta(seconds = 2))
def sample_job():
    print( "I will die only if OSError occurs, becouse of start function" )

tl.start(stop_on_exception = OSError)
```
## Mode to start jobs

### Start timeloop in a separate thread
By default timeloop starts in a separate thread. When it's in this mode do not forget to call `tl.stop()` before exiting the program, or else the jobs wont shut down gracefully (or they will even not shutdown).
```python
tl.start() or tl.start(block=False)
```

### Start time loop in the main thread
Doing this will automatically shut down the jobs gracefully when the program is killed, so no need to  call `tl.stop()`. The main thread that calls the `tl.start()` will be stuck until you kill him (kill command or Ctrl+C on shell).
```python
tl.start(block=True)
```
