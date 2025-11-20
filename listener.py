import json
import hashlib
import logging
import redis
import threading
import time
from datetime import datetime, timedelta
from django.conf import settings
from whatsapp.tasks import handle_incoming_message

logger = logging.getLogger('wa_listener')

# ============================================================
# REDIS CONFIG
# ============================================================
REDIS_SETTINGS = getattr(settings, 'redis', {})

REDIS_HOST = REDIS_SETTINGS.get('host', 'localhost')
REDIS_PORT = REDIS_SETTINGS.get('port', 6379)
REDIS_DB   = REDIS_SETTINGS.get('db', 15)
REDIS_PASS = REDIS_SETTINGS.get('password', None)
REDIS_CHANNEL = REDIS_SETTINGS.get('channel', 'whatsapp:inbox')

# Redis connection (no decode_responses → lebih cepat)
def redis_conn():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASS,
    )


# ============================================================
# ANTI DUPLICATE CACHE (20 detik)
# ============================================================
recent_hashes = {}
DUPLICATE_TTL = timedelta(seconds=20)


def is_duplicate_message(data: dict) -> bool:
    raw = json.dumps(data, sort_keys=True, separators=(',', ':'))
    msg_hash = hashlib.sha256(raw.encode()).hexdigest()
    now = datetime.now()

    # Cleanup hash lama
    expired = [h for h, ts in recent_hashes.items() if now - ts > DUPLICATE_TTL]
    for h in expired:
        del recent_hashes[h]

    if msg_hash in recent_hashes:
        return True

    recent_hashes[msg_hash] = now
    return False


# ============================================================
# REDIS SUBSCRIBER
# ============================================================
def redis_subscriber():
    '''
    Listener yang stabil:
    - Auto reconnect kalau Redis putus
    - Tidak exit bila ada error satu pesan
    '''
    while True:
        try:
            r = redis_conn()
            pubsub = r.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(REDIS_CHANNEL)

            logger.info(f'📡 Redis subscriber listening on channel: {REDIS_CHANNEL}')

            for message in pubsub.listen():
                if message.get('type') != 'message':
                    continue

                try:
                    raw = message['data']
                    if isinstance(raw, bytes):
                        raw = raw.decode('utf-8')

                    data = json.loads(raw)

                    # Anti duplikat
                    if is_duplicate_message(data):
                        logger.debug('⏩ Duplikat pesan diabaikan')
                        continue

                    logger.info('📨 Pesan baru diterima, dikirim ke worker Huey')
                    handle_incoming_message(data)

                except Exception as e:
                    logger.exception(f'⚠️ Error memproses pesan: {e}')

        except redis.exceptions.ConnectionError:
            logger.warning('❌ Redis connection lost → retry 2 detik...')
            time.sleep(2)

        except Exception as e:
            logger.exception(f'Fatal subscriber error: {e}')
            time.sleep(2)


# ============================================================
# START LISTENER (TIDAK BOLEH DOUBLE)
# ============================================================
_listener_started = False


def start_listener():
    global _listener_started
    if _listener_started:
        logger.debug('Redis listener already running → skip')
        return

    _listener_started = True

    t = threading.Thread(target=redis_subscriber, daemon=True)
    t.start()

    logger.info('🚀 Redis listener thread started')
