import datetime
import logging
import sys
import urllib

from pathlib import Path

from builder import settings, HookData, RefType, Ref, Url
from builder.deployment import DeployError
from builder.executor import BuildError
from builder.repo import Repo, Subproject
from builder.s3 import UploadError, ensure_buckets

logger = logging.getLogger('Main')

def get_repo_from_ssh_url(url: Url) -> Repo:
    for r in settings.REPOS:
        if r['GitUrl'] == url:
            return Repo.from_config(r)
    raise ValueError(f'Repo with url {url} is unknown')

def setup_file_logger(repo: Repo, ref: Ref):
    now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_fname = f'{now}-{repo.name}-{ref}.log'
    fh = logging.FileHandler(Path(settings.LOG_PATH) / log_fname)
    log_format ='%(asctime)-15s [%(levelname)5s] [%(name)s] %(message)s'
    fh.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(fh)
    return log_fname


def build_on_hook(hook_data: HookData):
    ref = hook_data.ref
    repo = get_repo_from_ssh_url(hook_data.repo_url)
    _ref = f'@{ref}' if ref != 'master' else ''
    log_fname = setup_file_logger(repo, ref)
    log_url = settings.LOG_URL.format(logfile=urllib.parse.quote(log_fname))

    logger.info(f'Starting build for {repo.name}')
    repo.notify(f'Starting build for {repo.name}{_ref}, you can find the logs at {log_url}')
    if len(hook_data.commits):
        logger.info(f'Commits in this build:')
        for commit in hook_data.commits:
            logger.info(commit)

    try:
        repo_dst = repo.fetch_at(ref)
        subprojects = Subproject.parse_from_config(repo_dst / 'build.json')
        for subproject in subprojects:
            artifacts = subproject.build()
            for artifact in artifacts:
                repo.upload_artifact(ref, subproject, artifact)
        repo.trigger_deployment(ref)
    except BuildError as e:
        repo.notify(f'Failure building {repo.name}: {e}')
        return
    except UploadError as e:
        repo.notify(f'Failure uploading {repo.name}: {e}')
        return
    except DeployError as e:
        repo.notify(f'Failure deploying {repo.name}: {e}')
        return

    repo.notify(f'Building {repo.name} succeeded')
