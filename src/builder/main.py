from builder import settings
from builder.s3 import UploadError
from builder.docker import BuildError
from builder.deployment import DeployError
from builder.repo import Repo, Subproject

import json


def work(repo, ref):
    try:
        repo_dst = repo.fetch_at(ref)
        subprojects = Subproject.parse_from_config(repo_dst / 'build.json')
        _ref = f'@{ref}' if ref != 'master' else ''
        repo.notify(f'Starting build for {repo.name}{_ref}, you can find the logs at PATH')
        for subproject in subprojects:
            artifacts = subproject.build()
            for artifact in artifacts:
                artifact.upload_and_delete_locally()
        repo.trigger_deployment()
        repo.notify(f'Building {repo.name} succeeded')
    except BuildError as e:
        repo.notify(f'Failure building {repo.name}: {e}')
    except UploadError as e:
        repo.notify(f'Failure uploading {repo.name}: {e}')
    except DeployError as e:
        repo.notify(f'Failure deploying {repo.name}: {e}')


for r in settings.REPOS:
    repo = Repo.from_config(r)
    print(repo)
    if repo.name == 'Test Repo':
        print(repo)
        work(repo, 'master')
