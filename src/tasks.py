import datetime
import os
import random
import time
import warnings
from threading import Thread, Event
from time import sleep
from app import celery_app

import numpy as np

from celery import group
from celery.utils.log import get_task_logger

from caching import get_client

KEY = "valuations"
logger = get_task_logger(__name__)


NO_BROKER_WARNING = "no celery broker configured -> using eager mode"
warnings.filterwarnings("once", NO_BROKER_WARNING)


@celery_app.task(name="tasks.add")
def add(x, y):
    logger.info('hello world')
    return x + y


@celery_app.task(name="tasks.sleeper")
def sleeper():
    sleep(2)
    logger.info("done sleeping")


class Calculator:

    def __init__(self, portfolio, scenario):
        print("creating calculator")
        self.portfolio = portfolio
        self.scenario = scenario

    def run(self, bucket, scenario):
        ...

def log_progress(n_scenarios, client, event_tasks_done: Event):
    """logs the progress of the evaluation tasks by evaluating the number of scenario data written."""

    format_length = len(str(n_scenarios)) - 1
    while True:
        time.sleep(2)
        if event_tasks_done.is_set():
            break
        if not client.exists(KEY):
            continue
        n_complete = client.hlen(KEY)
        progress = n_complete / n_scenarios * 100
        print(datetime.datetime.now(),
              f"[{n_complete:{format_length}}/{n_scenarios}] Done ({progress:.1f}%)")


class EvaluationTask(celery_app.Task):
    name = "tasks.EvaluationTask"

    def __init__(self):
        self.worker = None


    def initialize_worker(self, scenario):

        if not self.redis.exists("data"):
            raise RuntimeError("cannot start worker, no input data found in redis cache ('data'))")

        portfolio = self.redis.hget("data", "portfolio")
        logger.info(f"starting worker with scenario {scenario}")
        time.sleep(10)  # simulating the initial time needed to setup the worker.
        self.worker = portfolio

    def run(self, bucket, scenario):
        self.redis = get_client()
        if not self.worker:
            self.initialize_worker(scenario)

        time.sleep(random.expovariate(1))
        # simulate that an array of 17 indices is returned
        array = 0.1 * np.random.random(17) + scenario
        # noinspection PyTypeChecker
        self.redis.hset(KEY, scenario, array.tobytes())




celery_app.register_task(EvaluationTask)


@celery_app.task(name="tasks.batch")
def batch(n):
    """main task that will run several evaluation tasks"""

    client = get_client()
    client.delete("data")
    client.hset("data", mapping={"portfolio": np.array([1, 2, 3]).tobytes(), "scenario": "567"})

    # flush the redis values
    client.delete(KEY)

    done_event = Event()

    # create thread that logs progress
    log_thread = Thread(target=log_progress, args=(n, client, done_event,))
    log_thread.start()

    if not os.environ.get("CELERY_BROKER_URL"):
        # no celery backend -> run locally using always eager
        warnings.warn(NO_BROKER_WARNING, stacklevel=4)
        celery_app.conf.task_always_eager = True

    task = EvaluationTask()
    signatures = (task.si("bucket", x) for x in range(n))
    grouptask = group(signatures)()
    grouptask.get(disable_sync_subtasks=False)
    done_event.set()

    valuations = np.array([np.frombuffer(client.hget(KEY, i)) for i in range(n)])
    print(valuations)
    return len(valuations)


if __name__ == '__main__':

    # start the batch task
    from dotenv import load_dotenv


    load_dotenv()

    celery_app.conf.broker_url = os.environ["CELERY_BROKER_URL"]
    celery_app.conf.result_backend = os.environ["CELERY_RESULT_BACKEND"]

    print(batch(60))

    # print("calling batch via celery")
    # print(batch.delay(100).get())


