import logging
import multiprocessing
import os
import signal
import sys

import builder  # noqa - preload before forking

from functools import partial

from builder import settings
from builder.logger import setup_logging

from redis import StrictRedis
from rq import Connection, Worker

logger = logging.getLogger('Worker')

def kill_workers(workers, signum, frame):
    logger.info('Signal %s caught! Passing it down to workers..', signum)
    for worker in workers:
        os.kill(worker.pid, signal.SIGINT)

def start():
    setup_logging()
    with Connection(connection=StrictRedis()):
        workers = []

        for i in range(settings.WORKER_COUNT):
            p = multiprocessing.Process(target=Worker(settings.WORKER_QUEUE_NAME).work)
            p.start()
            workers.append(p)
        signal.signal(signal.SIGINT, partial(kill_workers, workers))
        signal.signal(signal.SIGTERM, partial(kill_workers, workers))

        for w in workers:
            p.join()

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    start()  # pyinstaller
