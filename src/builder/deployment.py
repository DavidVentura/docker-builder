import logging

import requests

from builder import Url
from builder import settings

from dataclasses import dataclass

logger = logging.getLogger('Deployment')

class DeployError(Exception):
    pass


class Deployer:
    def deploy(self, *args, **kwargs):
        raise NotImplementedError


@dataclass
class RESTDeployer(Deployer):
    url: str # Url

    def deploy(self, repo_name: str, ref: str):
        logger.info(f'Deploying {repo_name}@{ref}')
        url = settings.REST_DEPLOYER_URL.format(repo=repo_name, ref=ref)
        payload = {'secret': settings.REST_DEPLOYER_SECRET}
        r = requests.post(url, json=payload)
        try:
            r.raise_for_status()
        except Exception as e:
            logger.error(f'Failed deploying {repo_name}@{ref}!')
            logger.exception(e)
            raise DeployError(e)

        for line in r.text.splitlines():
            logger.info(line.strip())
        logger.info(f'Deploying {repo_name}@{ref} successful!')


@dataclass
class NullDeployer(Deployer):
    def deploy(self, *args, **kwargs):
        logger.info('NullDeployer asked to deploy... doing nothing')
