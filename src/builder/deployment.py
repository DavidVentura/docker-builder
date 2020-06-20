from dataclasses import dataclass

from builder import Url


class DeployError(Exception):
    pass


class Deployer:
    pass


@dataclass
class RemoteAnsibleDeployer(Deployer):
    url: 'Url'
