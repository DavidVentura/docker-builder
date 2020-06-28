import logging
import sys

import jsonschema
import waitress

from typing import List, NamedTuple

from builder import Url, HookData, Commit, settings, RefType
from builder.logger import setup_logging
from builder.schemas import WEBHOOK_SCHEMA
from builder.main import build_on_hook

from flask import url_for, request
from flask_api import FlaskAPI, status
from redis import StrictRedis
from rq import Queue

app = FlaskAPI(__name__)
q = Queue(settings.WORKER_QUEUE_NAME, connection=StrictRedis())
logger = logging.getLogger('Hook')


def _parse_hook(data):
    ref_type = RefType[data.get('ref_type', 'push')]
    commits = [Commit(c['timestamp'], c['id'], c['message']) for c in data.get('commits', [])]
    ref = data['ref'].split('/')[-1]
    hd = HookData(ref_type=ref_type,
            commits=commits,
            ref=ref,
            repo_url=data["repository"]["ssh_url"])
    return hd


@app.route("/webhook", methods=['POST'])
def deploy():
    data = request.json
    if data is None:
        return {'error': 'You must POST data according to the schema',
                'schema': WEBHOOK_SCHEMA}, status.HTTP_400_BAD_REQUEST

    try:
        jsonschema.validate(data, schema=WEBHOOK_SCHEMA)
    except Exception as e:
        return {'error': e.message, 'schema': WEBHOOK_SCHEMA}, status.HTTP_400_BAD_REQUEST

    hook_data = _parse_hook(data)
    logger.info(f'enqueueing {hook_data}')
    job = q.enqueue(build_on_hook, hook_data)
    return {}, status.HTTP_202_ACCEPTED


def start():
    setup_logging()
    waitress.serve(app, port=settings.WEBSERVER_PORT)
