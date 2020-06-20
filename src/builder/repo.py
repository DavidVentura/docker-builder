import json
import shutil

from builder import Ref, Url, settings
from builder.deployment import Deployer, RemoteAnsibleDeployer
from builder.executor import Artifact, BuildMode, run_build
from builder.notifications import Telegram, Notifier
from builder.s3 import upload_blob

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

import git

@dataclass
class Repo:
    name: str
    repo: 'Url'
    bucket: str
    notifier: 'Notifier'
    deployer: 'Deployer'

    @staticmethod
    def from_config(config):
        if 'TelegramChatId' in config:
            n = Telegram(chat_id=config['TelegramChatId'])
        else:
            raise NotImplementedError('Only telegram notifier has been implemented')
        
        if 'AnsibleDeployer' in config:
            d = RemoteAnsibleDeployer(url=config['AnsibleDeployer'])
        else:
            raise NotImplementedError('Only Ansible Deployer has been implemented')

        return Repo(name=config['Name'],
                repo=config['GitUrl'],
                bucket=config['Bucket'],
                notifier=n,
                deployer=d)

    def trigger_deployment(self):
        pass

    def fetch_at(self, ref: Ref) -> Path:
        # FIXME: acquire lock in enter/exit? repo-ref should be uniq at any given time
        path = Path(settings.CLONE_PATH) / self.name / ref
        shutil.rmtree(path)
        r = git.Repo.clone_from(self.repo, path)
        r.head.reference = ref
        return path

    def notify(self, msg):
        self.notifier.notify(msg)

    def upload_artifact(self, ref: str, subproject: 'Subproject', artifact: Artifact):
        # FIXME this doesn't feel like it belongs in repo.. but it also does not belong anywhere else
        print(f"Now I'd upload this to s3://{self.bucket}/")
        key = f'{ref}/{subproject.name}/{artifact.key}'
        upload_blob(artifact.data, self.bucket, key)

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

                subproject = Subproject(name=sp['name'],
                        absolute_path=repo_path / sp['dir'],
                        artifact_paths=artifacts)

                ret.append(subproject)
        return ret

    def build(self) -> List[Artifact]:
        return run_build(self.absolute_path, self.artifact_paths, self.build_mode)
