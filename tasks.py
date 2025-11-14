import json
import redis
import logging
from datetime import datetime
from django.conf import settings
from huey.contrib.djhuey import task

logger = logging.getLogger("wa_huey")

REDIS_KEY = "wa:inbox"
r = redis.Redis(host="localhost", port=6379, db=15)


@task()
def handle_incoming_message(data):
    try:
        key = data.get("key", {})
        sender = key.get("remoteJid", "unknown")
        msg_content = data.get("message", {})
        push_name = data.get("pushName", "-")

        logger.info(f"📩 Pesan masuk dari {push_name} ({sender})")

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

        # Import process_inbox di dalam fungsi (lazy import)
        from whatsapp.commands import process_inbox
        process_inbox(inbox)

    except Exception as e:
        logger.exception(f"❌ Gagal memproses pesan: {e}")


@task()
def async_fallback_reply(sender, text, device_id):
    import requests
    from whatsapp.commands import send_reply   # aman, ini tidak circular

    FALLBACK_URL = getattr(
        settings,
        "AI_AGENT_URL",
        "http://192.168.223.186:5678/webhook/user-request"
    )

    payload = {
        "query": {
            "user_id": sender,
            "message": text,
        }
    }

    logger.info(f"⏳ Mengirim ke AI Agent untuk {sender}...")

    try:
        res = requests.post(FALLBACK_URL, json=payload, timeout=60)

        if res.status_code == 200:
            try:
                response_data = res.json()
                if isinstance(response_data, list) and response_data:
                    message_text = response_data[0].get("message", "")
                else:
                    message_text = str(response_data)
            except Exception:
                message_text = res.text

            send_reply(sender, message_text, device_id)
            logger.info(f"🤖 Balasan AI berhasil untuk {sender}")
        else:
            logger.warning(f"❌ AI Agent error: {res.text}")

    except Exception as e:
        logger.error(f"AI Agent fallback error: {e}")
