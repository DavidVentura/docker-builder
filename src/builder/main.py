import logging

from builder import settings
from builder.s3 import UploadError, ensure_buckets
from builder.executor import BuildError
from builder.deployment import DeployError
from builder.repo import Repo, Subproject

import json

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('Main')

def work(repo, ref):
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
        repo.notify(f'Building {repo.name} succeeded')
    except BuildError as e:
        repo.notify(f'Failure building {repo.name}: {e}')
    except UploadError as e:
        repo.notify(f'Failure uploading {repo.name}: {e}')
    except DeployError as e:
        repo.notify(f'Failure deploying {repo.name}: {e}')


repos = [Repo.from_config(r) for r in settings.REPOS]
ensure_buckets([repo.bucket for repo in repos])
for repo in repos:
    if repo.name == 'Test Repo':
        print(repo)
        work(repo, 'master')
