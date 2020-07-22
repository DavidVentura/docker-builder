import datetime
import logging
import sys
import urllib

from pathlib import Path

from builder import settings, HookData, RefType, Ref, Url
from builder.deployment import DeployError
from builder.executor import BuildError
from builder.repo import Repo, Subproject
from builder.redis import job_conn
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
    Path(settings.LOG_PATH).mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(Path(settings.LOG_PATH) / log_fname)
    log_format ='%(asctime)-15s [%(levelname)5s] [%(name)s] %(message)s'
    fh.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(fh)
    return log_fname


def build_on_hook(hook_data: HookData):
    ref = hook_data.ref
    repo = get_repo_from_ssh_url(hook_data.repo_url)
    log_fname = setup_file_logger(repo, ref)
    log_url = settings.LOG_URL.format(logfile=urllib.parse.quote(log_fname))

    logger.info(f'Acquiring lock for {repo.name}')
    with job_conn.lock(repo.name):
        build(hook_data, ref, repo, log_url)

def build(hook_data: HookData, ref: Ref, repo: Repo, log_url: Url):
    _ref = f'@{ref}' if ref != 'master' else ''

    logger.info(f'Starting build for {repo.name}')
    ensure_buckets([repo.bucket])
    repo.notify(f'Starting build for {repo.name}{_ref}, you can find the logs at {log_url}')
    if len(hook_data.commits):
        logger.info(f'Commits in this build:')
        for commit in hook_data.commits:
            logger.info(f'{commit.timestamp} - {commit.ref} - {commit.msg}')

    try:
        logger.info(f'Fetching repo at <{ref}>')
        repo_dst = repo.fetch_at(ref)
        subprojects = Subproject.parse_from_config(repo_dst / 'build.json')
        for subproject in subprojects:
            logger.info(f'Found subproject: {subproject}')
            artifacts = subproject.build()
            for artifact in artifacts:
                repo.upload_artifact(ref, subproject, artifact)
        repo.trigger_deployment(ref)
    except BuildError as e:
        error = f'Failure building {repo.name}'
        logger.error(error)
        logger.error(e)
        repo.notify(error)
        return
    except UploadError as e:
        error = f'Failure uploading {repo.name}'
        logger.error(error)
        logger.error(e)
        repo.notify(error)
        return
    except DeployError as e:
        error = f'Failure deploying {repo.name}'
        logger.error(error)
        logger.error(e)
        repo.notify(error)
        return
    except Exception as e:
        error = f'Unhandled Failure while working on {repo.name}'
        logger.error(error)
        logger.error(e)
        repo.notify(error)
        return

    logger.info(f'Building {repo.name} succeeded')
    repo.notify(f'Building {repo.name} succeeded')
