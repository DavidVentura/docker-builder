import enum
import datetime

from typing import TypeVar, NamedTuple, List

from dynaconf import settings

Ref = TypeVar(str)
Url = TypeVar(str)

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
