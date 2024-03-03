import asyncio
import logging
import time
from datetime import timedelta
from typing import Dict, List

import pytest

from atevery import every, start_background_tasks, stop_background_tasks

RAN_TASKS: Dict[str, List[float]] = {}


@pytest.fixture(scope='function', autouse=True)
def reset_ran_tasks():
    global RAN_TASKS
    RAN_TASKS = {}


def register_running(task_name):
    RAN_TASKS.setdefault(task_name, []).append(time.monotonic())


def assert_max_diff(times: List[float], expected_diff: float) -> None:
    for a, b in zip(times, times[1:]):
        logging.getLogger('test').critical(f"{a} - {b}")
        assert abs(int(a - b)) <= expected_diff, \
            f'Failed asserting diff between ({a} - {b}) {a - b} <= {expected_diff}'


async def test_can_start_background_tasks():
    @every(timedelta(seconds=1))
    def recording_task():
        register_running(recording_task.__name__)

    @every(timedelta(seconds=1))
    async def async_recording_task():
        register_running(async_recording_task.__name__)

    @every(timedelta(seconds=1))
    async def non_quitting():
        register_running(non_quitting.__name__)
        await asyncio.sleep(timedelta(hours=15).total_seconds())

    await start_background_tasks()
    await asyncio.sleep(2.5)
    await stop_background_tasks()

    assert 2 <= len(RAN_TASKS[recording_task.__name__]), 'Should have run at least twice'
    assert_max_diff(RAN_TASKS[recording_task.__name__], 1)
    assert 2 <= len(RAN_TASKS[async_recording_task.__name__]), 'Should have run at least twice'
    assert_max_diff(RAN_TASKS[async_recording_task.__name__], 1)
    assert 1 == len(RAN_TASKS[non_quitting.__name__]), 'Should have run only once'


async def test_parameters():
    a = {}
    b = {}
    c = {}
    d = {}

    @every(timedelta(milliseconds=100), a, b=b)
    def param_task(a, b=None):
        a['received'] = True
        b['received'] = True

    @every(timedelta(milliseconds=100), c, b=d)
    async def async_param_task(a, b=None):
        a['received'] = True
        b['received'] = True

    await start_background_tasks()
    await asyncio.sleep(1)
    await stop_background_tasks()

    assert a['received']
    assert b['received']
    assert c['received']
    assert d['received']


def test_minimum_resolution():
    with pytest.raises(ValueError):
        @every(timedelta(milliseconds=49))
        def test():
            pass
