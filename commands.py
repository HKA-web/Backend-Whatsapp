import logging
import requests
from django.conf import settings

logger = logging.getLogger("wa_process")

# Endpoint Node.js
NODE_API_URL = getattr(settings, "NODE_API_URL", "http://localhost:3000/api/send-messages")

# Endpoint AI Agent
FALLBACK_URL = "http://192.168.223.186:5678/webhook/user-request"


def process_inbox(inbox):
    try:
        sender = inbox["inbox_by"]
        msg_data = inbox["data"]

        # Ambil device bot dari inbox jika ada
        device_id = inbox.get("data", {}).get("bot_device", {}).get("phone")

        # Ambil teks pesan
        message_obj = msg_data.get("message", {})
        text = (
            message_obj.get("conversation")
            or message_obj.get("extendedTextMessage", {}).get("text")
            or ""
        ).strip()

        # Respon sederhana
        reply = None
        if text.lower() == "ya":
            reply = "✅ Baik, data kamu akan diproses."
        elif text.lower() == "tidak":
            reply = "❌ Baik, proses dibatalkan."
        else:
            if device_id:
                fallback_payload = {
                    "query": {
                        "user_id": device_id,
                        "message": text
                    }
                }
                try:
                    res = requests.post(FALLBACK_URL, json=fallback_payload, timeout=10)
                    if res.status_code == 200:
                        try:
                            response_data = res.json()
                            if isinstance(response_data, list) and len(response_data) > 0:
                                message_text = response_data[0].get("message", "")
                            else:
                                message_text = str(response_data)
                        except Exception:
                            message_text = res.text
                        reply = f'{message_text}'
                    else:
                        logger.warning(f"Gagal kirim fallback: {res.text}")
                except Exception as e:
                    logger.error(f"Error kirim fallback ke {FALLBACK_URL}: {e}")
            else:
                logger.warning(f"Tidak ada device_id, pesan fallback tidak dikirim. Pesan: {text}")
        if reply:
            # Payload untuk Node.js
            payload = {"jid": sender, "message": reply, "_botDevice": device_id}

            # Tambahkan device_id ke query jika ada
            url = NODE_API_URL
            if device_id:
                url = f"{NODE_API_URL}?device={device_id}"

            try:
                res = requests.post(url, json=payload, timeout=10)
                if res.status_code == 200:
                    logger.info(f"Balasan terkirim ke {sender} via device={device_id or 'default'}")
                else:
                    logger.warning(f"Gagal kirim balasan ke Node.js: {res.text}")
            except Exception as e:
                logger.error(f"Error kirim balasan ke Node.js: {e}")
        else:
            pass
    except Exception as e:
        inbox_id = inbox.get("id", "unknown")
        logger.exception(f"Gagal memproses inbox ID={inbox_id}: {e}")
