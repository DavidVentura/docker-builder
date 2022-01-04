import json
import logging
import shutil

from builder import Ref, Url, settings
from builder.deployment import Deployer, RESTDeployer, NullDeployer
from builder.executor import Artifact, BuildMode, run_build
from builder.notifications import Telegram, Notifier, NullNotifier
from builder.s3 import upload_blob, download_blob, list_bucket_path

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

import git

logger = logging.getLogger(__name__)

@dataclass
class Repo:
    name: str
    repo_url: 'Url'
    bucket: str
    notifier: 'Notifier'
    deployer: 'Deployer'
    local_path: Optional[Path] = None

    @staticmethod
    def from_config(config):
        notifier = NullNotifier()
        deployer = NullDeployer()

        if 'Notifier' in config:
            if config['Notifier'] == 'Telegram':
                notifier = Telegram(chat_id=config['TelegramChatId'])
            else:
                raise NotImplementedError('Only Telegram notifier has been implemented')
        
        if 'Deployer' in config:
            if config['Deployer'] == 'REST':
                deployer = RESTDeployer(url=config.get('REST_DEPLOYER_URL', settings.REST_DEPLOYER_URL))
            else:
                raise NotImplementedError('Only REST Deployer has been implemented')

        return Repo(name=config['Name'],
                repo_url=config['GitUrl'],
                bucket=config['Bucket'],
                notifier=notifier,
                deployer=deployer)

    def trigger_deployment(self, ref: Ref):
        self.deployer.deploy(self.name, ref)

    def fetch_at(self, ref: Ref) -> Path:
        # FIXME: acquire lock in enter/exit? repo-ref should be uniq at any given time
        path = Path(settings.CLONE_PATH) / self.name / ref
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
        r = git.Repo.clone_from(self.repo_url, path)
        r.checkout(ref)
        self.local_path = path
        return path

    def notify(self, msg) -> None:
        self.notifier.notify(msg)

    def upload_artifact(self, ref: str, subproject: 'Subproject', artifact: Artifact):
        # FIXME this doesn't feel like it belongs in repo.. but it also does not belong anywhere else
        key = f'{subproject.name}/{ref}/{artifact.key}'
        logger.info(f"Uploading {artifact.key} to s3://{self.bucket}/{key}")
        upload_blob(blob=artifact.data, bucket=self.bucket, key=key)

    def populate_secrets(self, subproject: 'Subproject'):
        logger.info('Populating secrets for %s', subproject.name)
        secrets = list_bucket_path(self.bucket, f'{subproject.name}/secrets/')
        for key in secrets:
            logger.info('Populating secret %s for %s', key, subproject.name)
            blob = download_blob(bucket=self.bucket, key=key)
            relative_secret_path = key[len(f'{subproject.name}/secrets/'):]
            file_path = self.local_path / relative_secret_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open('wb') as fd:
                fd.write(blob)

@dataclass
class Subproject:
    name: str
    absolute_path: Path
    artifact_paths: List[Path]
    build_mode: Optional[BuildMode] = None

    @staticmethod
    def parse_from_config(config_path: Path) -> List['Subproject']:
        ret = []
        repo_path = config_path.parent
        with config_path.open() as fd:
            # FIXME: validate json with schema
            config = json.load(fd)
            for sp in config['subprojects']:
                artifacts = [Path(a) for a in sp['artifacts']]

                build_mode = BuildMode[sp.get('build_mode', BuildMode.DEFAULT.name).upper()]
                subproject = Subproject(name=sp['name'],
                        absolute_path=repo_path / sp['dir'],
                        artifact_paths=artifacts,
                        build_mode=build_mode)

                ret.append(subproject)
        return ret

    def build(self) -> List[Artifact]:
        return run_build(self.absolute_path, self.artifact_paths, self.build_mode)
