# Timeloop
Timeloop is a service that can be used to run periodic tasks after a certain interval.

![timeloop](http://66.42.57.109/timeloop.jpg)

Each job runs on a separate thread and when the service is shut down, it waits till all tasks currently being executed are completed.

Inspired by this blog [`here`](https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/)

## Installation
```sh
pip install timeloop
```

## Writing jobs
```python
import time

from timeloop import Timeloop
from datetime import timedelta

tl = Timeloop()

@tl.job(interval=timedelta(seconds=2))
def sample_job_every_2s():
    print( "2s job current time : {}".format(time.ctime()) )

@tl.job(interval=timedelta(seconds=5))
def sample_job_every_5s():
    print( "5s job current time : {}".format(time.ctime()) )


@tl.job(interval=timedelta(seconds=10))
def sample_job_every_10s():
    print( "10s job current time : {}".format(time.ctime()) )
```

## Writing swarm jobs with arguments
```python
@tl.job(interval=timedelta(seconds=5), swarm = True)
def sample_job(idx):
    print( "Task id: {} | time: {}".format(idx, time.ctime()) )

# example: queue jobs with different ids
for id in range(1, 3):
	sample_job(id)
```

## Writing jobs that stop himself if exception occurs
```python
@tl.job(interval=timedelta(seconds=2), exception = True)
def sample_job():
    print( "I will die if any Exception occurs,time : {}".format(time.ctime()) )

@tl.job(interval=timedelta(seconds=2), exception = AttributeError)
def sample_job():
    print( "I will die soon, but only if AttributeError occurs" )
    raise AttributeError

@tl.job(interval=timedelta(seconds=2))
def sample_job():
    print( "I will die only if OSError occurs, becouse of start function" )

tl.start(stop_on_exception = OSError)
```

## Start time loop in separate thread
By default timeloop starts in a separate thread.

Please do not forget to call ```tl.stop``` before exiting the program, Or else the jobs wont shut down gracefully.

```python
tl.start()

while True:
  try:
    time.sleep(1)
  except KeyboardInterrupt:
    tl.stop()
    break
```

## Start time loop in main thread
Doing this will automatically shut down the jobs gracefully when the program is killed, so no need to  call ```tl.stop```
```python
tl.start(block=True)
```

## Author
* **Sankalp Jonna**

Email me with any queries: [sankalpjonna@gmail.com](sankalpjonna@gmail.com).
