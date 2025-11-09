import json
import threading
import logging
import redis
import hashlib
from datetime import datetime, timedelta
from whatsapp.tasks import handle_incoming_message

logger = logging.getLogger("wa_listener")

REDIS_CHANNEL = "whatsapp:inbox"
REDIS_CONN = redis.Redis(host="localhost", port=6379, db=15)

# Cache pesan untuk anti-spam
recent_hashes = {}
DUPLICATE_TTL = timedelta(seconds=10)

# Flag global untuk memastikan hanya 1 listener berjalan
_listener_started = False


def is_duplicate_message(data: dict) -> bool:
    """
    Cek apakah pesan sudah pernah diterima dalam waktu singkat.
    """
    # Buat hash dari isi pesan agar unik berdasarkan konten
    raw = json.dumps(data, sort_keys=True)
    msg_hash = hashlib.md5(raw.encode()).hexdigest()
    now = datetime.now()

    # Bersihkan cache lama
    for h, ts in list(recent_hashes.items()):
        if now - ts > DUPLICATE_TTL:
            del recent_hashes[h]

    if msg_hash in recent_hashes:
        return True

    recent_hashes[msg_hash] = now
    return False


def redis_subscriber():
    """
    Dengarkan channel Redis dan panggil handle_incoming_message setiap pesan baru.
    """
    pubsub = REDIS_CONN.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(REDIS_CHANNEL)

    logger.info(f"📡 Listening Redis channel: {REDIS_CHANNEL}")

    for message in pubsub.listen():
        try:
            if message.get("type") != "message":
                continue

            # Parse data
            raw_data = message["data"]
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode("utf-8")

            data = json.loads(raw_data)

            # ✅ Hindari duplikasi pesan yang identik
            if is_duplicate_message(data):
                logger.debug("⏩ Duplikat pesan, diabaikan.")
                continue

            logger.info(f"📨 Pesan baru diterima di channel {REDIS_CHANNEL}")
            handle_incoming_message(data)

        except Exception as e:
            logger.exception(f"⚠️ Error memproses pesan Redis: {e}")


def start_listener():
    """
    Jalankan listener di thread terpisah agar tidak blokir proses utama.
    Hindari multiple start akibat Django reload (runserver).
    """
    global _listener_started
    if _listener_started:
        logger.info("⚙️ Redis listener sudah aktif, skip start ulang.")
        return

    _listener_started = True
    listener_thread = threading.Thread(target=redis_subscriber, daemon=True)
    listener_thread.start()
    logger.info("🚀 Redis listener thread started")
