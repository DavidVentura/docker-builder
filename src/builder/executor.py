import enum
import io
import tarfile
import uuid

import docker

from builder import Ref

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dynaconf import settings

class BuildMode(enum.Enum):
    NPM = 'npm'
    PYTHON = 'python'
    DEFAULT = 'npm'

class BuildError(Exception):
    pass

@dataclass
class Artifact:
    data: bytes
    key: str


def run_build(path: Path, artifact_paths: List[Path], build_mode: Optional[BuildMode] = None) -> List[Artifact]:
    client = docker.from_env()

    if build_mode:
        dockerfile = settings.DOCKERFILES.get(build_mode.name)
    else:
        dockerfile = settings.DOCKERFILES.get(BuildMode.DEFAULT.name)

    tag = uuid.uuid4()
    print(path)
    import shutil
    import os
    shutil.copyfile(dockerfile, path / 'Dockerfile')

    cli = docker.APIClient()
    image_id = None
    try:
        for stream_obj in cli.build(path=str(path), tag=tag, rm=True, decode=True):
            # rm=True is the default for `docker-build`
            # but not for docker-py, as it would break backwards compat
            if 'stream' in stream_obj:
                msg = stream_obj['stream']
                print(msg.strip())
            elif 'errorDetail' in stream_obj:
                exit_code = stream_obj['errorDetail']['code']
                exit_msg = stream_obj['errorDetail']['message']
                raise BuildError(f'{exit_msg}\nExit code: {exit_code}')
            elif 'aux' in stream_obj:
                image_id = stream_obj['aux']['ID']
    except docker.errors.BuildError as e:
        raise BuildError(e)

    assert image_id is not None, "Did not get an image id from build?"

    container = client.containers.create(image_id)

    resulting_artifacts = []
    for artifact_path in artifact_paths:
        try:
            tarball, stat = container.get_archive(path=f'/usr/src/app/{artifact_path}')
        except docker.errors.NotFound as e:
            raise BuildError(e.explanation)

        buf = io.BytesIO()
        for chunk in tarball:
            buf.write(chunk)
        buf.seek(0, os.SEEK_SET)  # seek_set == beginning of file
        _tarfile = tarfile.open(fileobj=buf)  # tarfilne needs .tell(); docker gives a generator
        resulting_blob = _tarfile.next().tobuf()
        assert _tarfile.next() is None, "There were multiple files in the docker copy. What?"
        resulting_artifacts.append(Artifact(data=resulting_blob, key=artifact_path))

    container.remove(force=True)
    return resulting_artifacts
