import enum

from builder import Ref

from pathlib import Path
from typing import List, Optional

class BuildMode(enum.Enum):
    NPM = enum.auto()
    PYTHON = enum.auto()

class BuildError(Exception):
    pass

class Artifact:
    def __init__(self, local_fname, bucket, key):
        pass

    def upload_and_delete_locally(self):
        pass


def run_build(path: Path, artifact_paths: List[Path], build_mode: Optional[BuildMode] = None) -> List[Artifact]:
    return []
