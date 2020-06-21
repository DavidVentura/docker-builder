import logging

import requests

from typing import NamedTuple

from builder import Url
from builder import settings

logger = logging.getLogger('Deployment')

class DeployError(Exception):
    pass


class Deployer:
    def deploy(self):
        raise NotImplementedError


class RemoteAnsibleDeployer(Deployer, NamedTuple):
    url: Url

    def deploy(self, repo_name: str, ref: str):
        logger.info(f'Deploying {repo_name}@{ref}')
        url = settings.ANSIBLE_DEPLOYER_URL.format(repo=repo_name, ref=ref)
        payload = {'secret': settings.ANSIBLE_DEPLOYER_SECRET}
        r = requests.post(url, json=payload)
        try:
            r.raise_for_status()
        except Exception as e:
            logger.error(f'Failed deploying {repo_name}@{ref}!')
            logger.exception(e)
            raise DeployError(e)

        logger.info(f'Deploying {repo_name}@{ref} successful!')
