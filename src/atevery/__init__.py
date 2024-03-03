import asyncio
import time
from datetime import timedelta
from functools import partial
from typing import Optional, Set, List

REGISTERED_TASKS: List['PeriodicTask'] = []
RUNNING: Set['PeriodicTask'] = set()
RUNNING_FUTURES: Set[asyncio.Task] = set()
SHUTDOWN: bool = False
MINIMUM_RESOLUTION: timedelta = timedelta(milliseconds=50)


class PeriodicTask:

    def __init__(self, interval: timedelta, target, args, kwargs):
        if interval < MINIMUM_RESOLUTION:
            raise ValueError(f'interval must be greater than or equal to 50ms, was {interval}')
        self.interval_secs = interval.total_seconds()
        self.target = target
        self.target_iscorofunc = asyncio.iscoroutinefunction(target)
        self.args = args
        self.kwargs = kwargs
        self.next_at = time.monotonic()

    def should_run_now(self) -> bool:
        return self.next_at <= time.monotonic()

    async def run(self):
        self.next_at += self.interval_secs

        if self.target_iscorofunc:
            return await self.target(*self.args, **self.kwargs)

        return self.target(*self.args, **self.kwargs)


def every(interval: timedelta, /, *args, **kwargs):
    def periodic(func):
        REGISTERED_TASKS.append(PeriodicTask(interval, func, args, kwargs))
        return func

    return periodic


def done(task, future):
    RUNNING.discard(task)
    RUNNING_FUTURES.discard(future)


async def scheduler():
    while not SHUTDOWN:
        for task in REGISTERED_TASKS:
            if task in RUNNING or not task.should_run_now():
                continue

            RUNNING.add(task)
            future = asyncio.create_task(task.run(), name=f'atevery.task@{hash(task)}')
            RUNNING_FUTURES.add(future)
            future.add_done_callback(partial(done, task))

        await asyncio.sleep(MINIMUM_RESOLUTION.total_seconds())


async def start_background_tasks():
    global SHUTDOWN
    SHUTDOWN = False
    scheduler_task = asyncio.create_task(scheduler(), name='atevery.periodic_tasks')
    scheduler_task.add_done_callback(RUNNING_FUTURES.discard)
    RUNNING_FUTURES.add(scheduler_task)


async def stop_background_tasks(wait_for: bool = True, timeout: Optional[timedelta] = None):
    global SHUTDOWN
    SHUTDOWN = True
    if wait_for:
        for future in RUNNING_FUTURES:
            future.cancel()
        await asyncio.wait(RUNNING_FUTURES, timeout=timeout.total_seconds() if timeout else None)


__all__ = ['every', 'start_background_tasks', 'stop_background_tasks']
