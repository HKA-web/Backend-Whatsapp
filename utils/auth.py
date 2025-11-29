from pathlib import Path
from django.conf import settings
import yaml
from utils.sslinogre import *

def LoadWebhookAuth():
    config_path = Path(settings.BASE_DIR) / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['webhook']['access']

def Auth():
    BASE_URL = settings.WEBHOOK_URL.rstrip('/')
    payload = {
        'user_name': settings.WEBHOOK_USER,
        'password': settings.WEBHOOK_PASS
    }

    try:
        res = post_ignore_ssl(f'{BASE_URL}/api/token/', json=payload, timeout=30)

        if res.status_code != 200:
            return False

        try:
            response = res.json()
        except Exception:
            logger.error(f'[AUTH] Response bukan JSON: {res.text}')
            return False

        refresh_token = response.get('refresh')
        access_token  = response.get('access')

        if not refresh_token or not access_token:
            return False

        config_path = Path(settings.BASE_DIR) / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        config['webhook']['refresh'] = refresh_token
        config['webhook']['access']  = access_token

        with open(config_path, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False)

        return True

    except Exception as e:
        logger.exception(f'Auth token error: {e}')
        return False