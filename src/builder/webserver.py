import logging

import jsonschema
import waitress

from typing import List, NamedTuple

from builder import Url, HookData, Commit
from builder.schemas import WEBHOOK_SCHEMA

from flask_api import FlaskAPI, status
from redis import StrictRedis
from rq import Queue as Rqueue

app = FlaskAPI(__name__)
q = Rqueue(connection=StrictRedis())
logger = logging.getLogger('Hook')


def _parse_hook(data):
    ref_type = RefType[data.get('ref_type', 'push')]
    commits = [Commit(c['timestamp'], c['id'], c['message']) for c in data.get('commits', [])]
    hd = HookData(ref_type=ref_type,
            commits=commits,
            ref=data['ref'],
            repo_url=data["repository"]["ssh_url"])
    return hd


@app.route("/webhook", methods=['POST'])
def deploy():
    data = request.json
    if data is None:
        return {}, status.HTTP_400_BAD_REQUEST

    try:
        jsonschema.validate(data, schema=WEBHOOK_SCHEMA)
    except Exception as e:
        return {'error': str(e)}, status.HTTP_400_BAD_REQUEST

    hook_data = _parse_hook(data)
    job = q.enqueue(work, hook_data)
    return {}, status.HTTP_202_ACCEPTED


def serve():
    pass
