import datetime
import os
import random
import time
from threading import Thread, Event
from time import sleep
from app import celery_app

# if __name__ == '__main__':
#     from dotenv import load_dotenv
#     load_dotenv()
#
#     celery_app.conf.broker_url = os.environ["CELERY_BROKER_URL"]
#     celery_app.conf.result_backend = os.environ["CELERY_RESULT_BACKEND"]


import numpy as np

from celery.utils.log import get_task_logger

from caching import get_client

KEY = "valuations"
logger = get_task_logger(__name__)


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

def log_progress(n_scenarios, event_tasks_done: Event):
    """logs the progress of the evaluation tasks by evaluating the number of scenario data written."""

    client = get_client()

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

    def initialize(self):

        # portolio, scenario = self.cache_client.hget()
        ...

    def run(self, bucket, scenario):

        self.cache_client = get_client()
        # if not self.worker:
        #     self.initialize_worker()




        time.sleep(random.expovariate(1))
        # simulate that an array of 17 indices is returned
        array = 0.1 * np.random.random(17) + scenario
        # noinspection PyTypeChecker
        self.cache_client.hset(KEY, scenario, array.tobytes())




celery_app.register_task(EvaluationTask)


@celery_app.task(name="tasks.batch")
def batch():
    """main task that will run several evaluation tasks"""

    n = 100

    eval_task = EvaluationTask()
    out = eval_task.delay(2, 3).get(disable_sync_subtasks=False)
    print(out)

if __name__ == '__main__':

    # start the batch task
    from dotenv import load_dotenv
    from celery import group

    load_dotenv()

    celery_app.conf.broker_url = os.environ["CELERY_BROKER_URL"]
    celery_app.conf.result_backend = os.environ["CELERY_RESULT_BACKEND"]

    n = 100
    client = get_client()
    client.hset("data", mapping={"portfolio": "123", "scenario": "567"})


    # flush the redis values
    client.delete(KEY)

    done_event = Event()


    # create thread that logs progress
    log_thread = Thread(target=log_progress, args=(n, done_event,))
    log_thread.start()

    task = EvaluationTask()

    class LocalGroup:

        def __init__(self, signatures):
            self.signatures = signatures

        def get(self):

            for s in self.signatures:
                s()

    signatures = (task.si("foo", x) for x in range(n))
    if os.environ["CELERY_RESULT_BACKEND"]:
        grouptask = group(signatures)()
    else:
        grouptask = LocalGroup(signatures)

    grouptask.get()
    done_event.set()

    valuations = np.array([np.frombuffer(client.hget(KEY, i)) for i in range(n)])
    print(valuations)

