# atevery

A periodic task scheduler for asyncio processes.


## Installation options

```bash
pip install atevery
```
```bash
poetry add atevery
```

## Usage

Register entrypoint functions to be run periodically by using the `@every` decorator:

```python
from datetime import timedelta, datetime

from atevery import every

@every(timedelta(seconds=2), 'fast')
def print_time(name):
    print(name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
```

Then start the scheduler in the main entrypoint:

```python
import asyncio

from atevery import start_background_tasks, stop_background_tasks

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(start_background_tasks())
        loop.run_until_complete(...) # or loop.run_forever()
    finally:
        loop.run_until_complete(stop_background_tasks())
```

The registered functions are ran accordingly to their specified interval. Arguments and keyword
arguments passed to the `@every` decorator are forwarded to the target function.

The target function can also be a coroutine/async function, like:

```python
from datetime import timedelta, datetime

from atevery import every

@every(timedelta(seconds=2), 'fast')
async def print_time(name):
    print(name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
```

### Stopping and resuming tasks

Tasks can be stopped and restarted at any time by using the `stop_background_tasks` and `start_background_tasks`
functions. While stopping, tasks that are still running or pending to run are cancelled, and by default waited for. If
by any reason you don't want to cancel or wait for them, specify the `wait_for=False` or
`wait_for=True, timeout=timedelta(...)` arguments to the `stop_background_tasks` function.

### Concurrency

You can expect only a single instance of the same task to be running at the same time. In other words, the tasks are
only started once their last execution was finished.

```python
import asyncio
import random
from datetime import datetime, timedelta

from atevery import every, start_background_tasks, stop_background_tasks


@every(timedelta(seconds=2), 'slow')
async def print_time(name):
    print(name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    await asyncio.sleep(4)


async def run():
    while True:
        await asyncio.sleep(random.random())


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(start_background_tasks())
        loop.run_until_complete(run())
    finally:
        loop.run_until_complete(stop_background_tasks())
        loop.stop()
```

Outputs something similar to:

```text
slow 2024-03-03 14:24:26
slow 2024-03-03 14:24:30
slow 2024-03-03 14:24:34
slow 2024-03-03 14:24:38
```


### Commitment

The scheduler mechanism makes its best to keep committed to the requested interval, but some delay might happen,
specially under heavier loads. It comes from the fact the scheduler competes with the tasks and all other processes for
the CPU time.

In order to reduce the event loop and CPU pressure, the scheduler has a minium resolution of 50ms. That means that on
every iteration, the scheduler sleeps for 50ms. Attempting to schedule a task for intervals smaller than 50ms result in
`ValueError` being raised.

## Contributing

Feel free to create issues or merge requests with any improvement or fix you might find useful.
