import asyncio
import random
from datetime import datetime, timedelta

from atevery import every, start_background_tasks, stop_background_tasks


@every(timedelta(seconds=2), 'fast')
def print_time(name):
    print(name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


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
