import logging
import requests
from django.conf import settings

logger = logging.getLogger("wa_process")

NODE_API_URL = getattr(settings, "NODE_API_URL", "http://localhost:3000/api/send-messages")


def process_inbox(inbox):
    try:
        sender = inbox["inbox_by"]
        msg_data = inbox["data"]
        device_id = msg_data.get("bot_device", {}).get("phone")

        text = (
            msg_data.get("message", {}).get("conversation")
            or msg_data.get("message", {}).get("extendedTextMessage", {}).get("text")
            or ""
        ).strip()

        reply = None

        # Reply lokal
        if text.lower() == "ya":
            reply = "✅ Baik, data kamu akan diproses."
        elif text.lower() == "tidak":
            reply = "❌ Baik, proses dibatalkan."
        else:
            # Import async_fallback_reply di dalam fungsi (lazy import)
            from whatsapp.tasks import async_fallback_reply
            async_fallback_reply(sender, text, device_id)

            logger.info("Fallback request dikirim ke Huey (async)")
            return

        # Jika ada reply lokal, langsung kirim
        if reply:
            send_reply(sender, reply, device_id)

    except Exception as e:
        inbox_id = inbox.get("id", "unknown")
        logger.exception(f"Gagal memproses inbox ID={inbox_id}: {e}")


def send_reply(sender, message, device_id):
    payload = {"jid": sender, "message": message, "_botDevice": device_id}

    url = NODE_API_URL if not device_id else f"{NODE_API_URL}?device={device_id}"

    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            logger.info(f"Balasan terkirim ke {sender} via device={device_id or 'default'}")
        else:
            logger.warning(f"Gagal kirim balasan ke Node.js: {res.text}")
    except Exception as e:
        logger.error(f"Error kirim balasan ke Node.js: {e}")
