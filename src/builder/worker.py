import logging
import multiprocessing
import os
import signal
import sys

import builder  # noqa - preload before forking

from functools import partial

from builder import settings
from builder.redis import job_conn
from builder.logger import setup_logging

from rq import Connection, Worker

logger = logging.getLogger('Worker')

def kill_workers_and_myself(workers, signum, frame):
    logger.info('Signal %s caught!', signum)
    logger.info('Sending SIGINT to workers..')
    for worker in workers:
        os.kill(worker.pid, signal.SIGINT)
    logger.info('Re-starting myself')
    os.execv(sys.argv[0], sys.argv)

def start():
    setup_logging()
    with Connection(connection=job_conn):
        workers = []

        signal.signal(signal.SIGHUP, partial(kill_workers_and_myself, workers))

        logger.info('Starting workers on queue %s', settings.WORKER_QUEUE_NAME)
        for i in range(settings.WORKER_COUNT):
            p = multiprocessing.Process(target=Worker(settings.WORKER_QUEUE_NAME).work)
            p.start()
            workers.append(p)

        for w in workers:
            p.join()
