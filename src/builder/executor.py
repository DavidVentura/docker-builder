import enum
import gzip
import io
import logging
import os
import shutil
import tarfile
import uuid

import docker

from builder import Ref

from pathlib import Path
from typing import List, Optional, NamedTuple

from dynaconf import settings

logger = logging.getLogger('Executor')

class BuildMode(enum.Enum):
    NPM = 'npm'
    PYTHON = 'python'
    YARN = 'yarn'
    CUSTOM = 'custom'
    DEFAULT = 'npm'

class BuildError(Exception):
    pass

class Artifact(NamedTuple):
    data: bytes
    key: str


def buildmode_to_dockerfile(build_mode: Optional[BuildMode] = None) -> Optional[Path]:
    if build_mode == BuildMode.CUSTOM:
        return None
    if build_mode is None:
        return settings.DOCKERFILES.get(BuildMode.DEFAULT.name)

    if build_mode.name not in settings.DOCKERFILES:
        raise BuildError(f'Requested build mode `{buld_mode}` is not configured in settings')

    return settings.DOCKERFILES[build_mode.name]


def run_build(path: Path, artifact_paths: List[Path], build_mode: Optional[BuildMode] = None) -> List[Artifact]:
    dockerfile = buildmode_to_dockerfile(build_mode)
    if dockerfile:
        shutil.copyfile(dockerfile, path / 'Dockerfile')

    tag = uuid.uuid4()
    cli = docker.APIClient()
    client = docker.from_env()
    image_id = None
    try:
        for stream_obj in cli.build(path=str(path), tag=tag, rm=True, decode=True):
            # rm=True is the default for `docker-build`
            # but not for docker-py, as it would break backwards compat
            if 'stream' in stream_obj:
                msg = stream_obj['stream']
                logger.info(msg.strip())
            elif 'errorDetail' in stream_obj:
                exit_code = stream_obj['errorDetail'].get('code', 'Unknown')
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

        logger.info(f'Artifact stat: {stat}')

        buf = io.BytesIO()
        for chunk in tarball:
            buf.write(chunk)

        buf.seek(0, os.SEEK_SET)  # seek_set == beginning of file
        _tarfile = tarfile.open(fileobj=buf)  # tarfilne needs .tell(); docker gives a generator
        members = _tarfile.getmembers()
        
        if len(members) == 1:
            logger.info('Unpacking single-item tar file')
            member = _tarfile.getmember(stat['name'])
            resulting_blob = _tarfile.extractfile(member)
        else:
            logger.info('The artifact was a directory - returning compressed')
            buf.seek(0, os.SEEK_SET)  # seek_set == beginning of file
            resulting_blob = gzip.compress(buf.read(), compresslevel=6)
            artifact_path = f'{artifact_path}.tar.gz'

        resulting_artifacts.append(Artifact(data=resulting_blob, key=artifact_path))

    container.remove(force=True)
    return resulting_artifacts
