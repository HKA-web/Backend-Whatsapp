import json
import redis
import logging
from datetime import datetime
from huey import crontab
from huey.contrib.djhuey import task, periodic_task
from whatsapp.commands import process_inbox

logger = logging.getLogger("wa_huey")

REDIS_KEY = "wa:inbox"
r = redis.Redis(host="localhost", port=6379, db=15)

# ========================
# 1️⃣ Tugas utama: proses pesan
# ========================
@task()
def handle_incoming_message(data):
    """Proses satu pesan WhatsApp"""
    try:
        key = data.get("key", {})
        sender = key.get("remoteJid", "unknown")
        msg_content = data.get("message", {})
        push_name = data.get("pushName", "-")

        logger.info(f"📩 Pesan masuk dari {push_name} ({sender})")

        # === Simpan inbox sementara (tanpa DB)
        inbox = {
            "id": int(datetime.now().timestamp()),
            "inbox_by": sender,
            "message": json.dumps(msg_content, indent=2),
            "message_type": "conversation",
            "data": data,
            "received_at": datetime.now().isoformat(),
            "processed": False,
            "reply_message": None,
        }

        process_inbox(inbox)

    except Exception as e:
        inbox_id = inbox.get("id", "unknown") if isinstance(inbox, dict) else "unknown"
        logger.exception(f"❌ Gagal memproses inbox ID={inbox_id}: {e}")
