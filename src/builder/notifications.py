import logging

import requests

from dataclasses import dataclass

from builder import settings

logger = logging.getLogger('Notifier')

class Notifier:
    def __init__(self):
        raise NotImplementedError

    def notify(self, msg: str):
        raise NotImplementedError

@dataclass
class Telegram(Notifier):
    chat_id: int

    def notify(self, msg: str):
        key = settings.TELEGRAM_BOT_KEY
        url = f"https://api.telegram.org/bot{key}/sendMessage"
        payload = {'chat_id': self.chat_id, 'text': msg}
        r = requests.post(url, json=payload)
        r.raise_for_status()

@dataclass
class NullNotifier(Notifier):
    def notify(self, msg: str):
        logger.info(f'NullNotifier got msg: {msg}')
