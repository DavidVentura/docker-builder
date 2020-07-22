from builder import settings
from redis import StrictRedis
from rq import Queue
job_conn = StrictRedis()
q = Queue(settings.WORKER_QUEUE_NAME, connection=job_conn)
