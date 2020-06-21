import logging

from builder import settings, HookData, RefType
from builder.s3 import UploadError, ensure_buckets
from builder.executor import BuildError
from builder.deployment import DeployError
from builder.repo import Repo, Subproject
from builder.webserver import serve
from builder.worker import work

logging.basicConfig(level=logging.INFO, format='%(asctime)-15s [%(levelname)5s] [%(name)s] %(message)s')
log = logging.getLogger('Main')

def entrypoint():
    repos = [Repo.from_config(r) for r in settings.REPOS]
    ensure_buckets([repo.bucket for repo in repos])

if __name__ == '__main__':
    repos = [Repo.from_config(r) for r in settings.REPOS]
    ensure_buckets([repo.bucket for repo in repos])
    for repo in repos:
        if repo.name == 'Test Repo':
            print(repo)
            hd = HookData(ref_type=RefType.push, commits=[], ref='master', repo_url=repo.repo_url)
            work(hd)
