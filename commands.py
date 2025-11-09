import logging
import requests
from django.conf import settings

logger = logging.getLogger("wa_process")

NODE_API_URL = getattr(settings, "NODE_API_URL", "http://localhost:3000/send-messages")


def process_inbox(inbox):
    """Respon sederhana berdasarkan pesan."""
    try:
        sender = inbox["inbox_by"]
        msg_data = inbox["data"]

        message_obj = msg_data.get("message", {})
        text = (
            message_obj.get("conversation")
            or message_obj.get("extendedTextMessage", {}).get("text")
            or ""
        ).strip().lower()

        # Logika sederhana
        if text == "ya":
            reply = "✅ Baik, data kamu akan diproses."
        elif text == "tidak":
            reply = "❌ Baik, proses dibatalkan."
        else:
            logger.info("💤 Pesan bukan 'ya' atau 'tidak', diabaikan.")
            return

        # Kirim balasan ke Node.js
        payload = {"jid": sender, "message": reply}
        try:
            res = requests.post(NODE_API_URL, json=payload, timeout=10)
            if res.status_code == 200:
                logger.info(f"✅ Balasan terkirim ke {sender}")
            else:
                logger.warning(f"⚠️ Gagal kirim balasan: {res.text}")
        except Exception as e:
            logger.error(f"🚨 Error kirim balasan ke Node.js: {e}")

    except Exception as e:
        inbox_id = inbox.get("id", "unknown")
        logger.exception(f"❌ Gagal memproses inbox ID={inbox_id}: {e}")
