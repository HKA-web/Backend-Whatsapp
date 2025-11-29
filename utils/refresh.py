from pathlib import Path
from django.conf import settings
import yaml
from utils.sslinogre import *

def LoadWebhookRefresh():
    config_path = Path(settings.BASE_DIR) / "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config["webhook"]["refresh"]

def Refresh():
    BASE_URL = settings.WEBHOOK_URL.rstrip('/')
    payload = {"refresh": LoadWebhookRefresh()}

    try:
        res = post_ignore_ssl(f"{BASE_URL}/api/refresh/", json=payload, timeout=30)

        if res.status_code != 200:
            return False

        try:
            response = res.json()
        except Exception:
            logger.error(f"[REFRESH] Response bukan JSON: {res.text}")
            return False

        refresh_token = response.get("refresh")
        access_token  = response.get("access")

        if not refresh_token or not access_token:
            return False

        config_path = Path(settings.BASE_DIR) / "config.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        config["webhook"]["refresh"] = refresh_token
        config["webhook"]["access"]  = access_token

        with open(config_path, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False)

        return True

    except Exception as e:
        logger.exception(f"Refresh token error: {e}")
        return False