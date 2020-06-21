import logging

from builder import HookData, Url, settings
from builder.s3 import UploadError
from builder.repo import Repo, Subproject
from builder.executor import BuildError
from builder.deployment import DeployError

logger = logging.getLogger('Worker')

def get_repo_from_ssh_url(url: Url) -> Repo:
    for r in settings.REPOS:
        if r['GitUrl'] == url:
            return Repo.from_config(r)
    raise ValueError(f'Repo with url {url} is unknown')

def work(hook_data: HookData):
    ref = hook_data.ref
    repo = get_repo_from_ssh_url(hook_data.repo_url)
    logger.info(f'Starting build for {repo.name}')
    if len(hook_data.commits):
        logger.info(f'Commits in this build:')
        for commit in hook_data.commits:
            logger.info(commit)

    try:
        repo_dst = repo.fetch_at(ref)
        subprojects = Subproject.parse_from_config(repo_dst / 'build.json')
        _ref = f'@{ref}' if ref != 'master' else ''
        repo.notify(f'Starting build for {repo.name}{_ref}, you can find the logs at PATH')
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
