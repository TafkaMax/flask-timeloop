# Timeloop
Timeloop is a service that can be used to run periodic tasks after a certain interval.

Each job runs on a separate thread and when the service is shut down, it waits till all tasks currently being executed are completed.

Forked and enhanced from [`here`](https://github.com/sankalpjonn/timeloop.git)

## Installation
Clone and install
```sh
git clone https://github.com/Ruggiero-Santo/timeloop.git
sudo python setup.py install
```

Direct installation 
```sh
pip install git+git://github.com/Ruggiero-Santo/timeloop.git
# or
pip install git+https://github.com/Ruggiero-Santo/timeloop.git
```

# Usage

## Writing jobs
```python
import time

from timeloop import Timeloop
from datetime import timedelta

tl = Timeloop()

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
In the job declared with  ```swarm = True``` the param ```interval``` can be omitted. This allows you to create a swarm of job with different interval, including ```interval = 2``` or ```interval = timedelta(seconds = 2)``` in the creation, like example.
```python
@tl.job(swarm = True)
def sample_job(idx):
    print( "Task id: {} | time: {}".format(idx, time.ctime()) )

# example: same jobs with different interval
for id in range(1, 3):
	sample_job(id, interval = id)
```

## Writing jobs that stop himself if exception occurs
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

### Start time loop in separate thread
By default timeloop starts in a separate thread. When it's in this mode do not forget to call ```tl.stop``` before exiting the program, Or else the jobs wont shut down gracefully (or they will not shutdown even).
```python
tl.start() or tl.start(block=False)
```

### Start time loop in main thread
Doing this will automatically shut down the jobs gracefully when the program is killed, so no need to  call ```tl.stop```. The main thread that call the ```tl.start``` will be stuck until you kill him (kill command or Ctrl+C on shell).
```python
tl.start(block=True)
```