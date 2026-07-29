import os

import requests
from dotenv import load_dotenv

load_dotenv()


def notify(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL が設定されていません。")

    response = requests.post(
        webhook_url,
        json={"content": message},
        timeout=10,
    )

    response.raise_for_status()