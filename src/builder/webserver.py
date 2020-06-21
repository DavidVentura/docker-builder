from builder import Url
from builder.schemas import WEBHOOK_SCHEMA

from typing import List, NamedTuple
from typing_extensions import Literal

import enum
import datetime
import json

import jsonschema

def hook_endpoint():
    data = request.json
    work(repo, ref)


class RefType(enum.Enum):
    push = enum.auto()
    tag = enum.auto()
    branch = enum.auto()

class Commit(NamedTuple):
    timestamp: datetime.datetime
    ref: str
    msg: str

class HookData(NamedTuple):
    ref_type: RefType
    commits: List[Commit]
    ref: str
    repo_url: Url

def parse_hook(data):
    jsonschema.validate(data, schema=WEBHOOK_SCHEMA)

    ref_type = data.get('ref_type', 'push')
    if ref_type != 'push':
        print(f'This was not just a push, was a {data["ref_type"]}')

    if ref_type == 'push' and 'commits' not in data:
        raise ValueError('Got a PUSH event with no commits!')

    print(f'Ref: {data["ref"]}')
    for commit in data.get('commits', []):
       print(f'{commit["timestamp"]} {commit["id"]}: {commit["message"]}')
    print(f'{data["repository"]["ssh_url"]}')
