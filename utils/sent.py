from pathlib import Path
from django.conf import settings
import yaml
from utils.sslinogre import *

def SendMessage(token, body):
    BASE_URL = settings.WEBHOOK_URL.rstrip('/')
    MESSAGE_URL = f'{BASE_URL}/whatsapp/api/outbox/'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        res = post_ignore_ssl(MESSAGE_URL, json=body, headers=headers, timeout=30)

        # Jika tidak bisa connect / timeout
        if res is None:
            return {'success': False, 'status': 0, 'data': None}

        # Berhasil (200 atau 201)
        if res.status_code in (200, 201):
            try:
                data = res.json()
            except:
                data = res.text
            return {'success': True, 'status': res.status_code, 'data': data}

        # Gagal biasa
        return {
            'success': False,
            'status': res.status_code,
            'data': res.text
        }

    except Exception as e:
        logger.exception(f'send_message error: {e}')
        return {'success': False, 'status': -1, 'data': str(e)}