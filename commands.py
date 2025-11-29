import logging
from django.conf import settings
from django.utils import timezone
from whatsapp.models.inbox import Inbox

logger = logging.getLogger("wa_command")


def process_inbox(inbox):
    try:
        # Import di sini untuk menghindari circular import
        from whatsapp.tasks import async_fallback_reply, process, ai_reply

        sender = inbox.get("inbox_by")
        msg_data = inbox.get("data", {}) or {}

        text = (msg_data.get("text") or "").strip()
        device_id = msg_data.get("bot_device", {}).get("phone")

        # ===== RULES =====
        if text.lower() == "backend":
            return "✅ Hai, aku backend."

        inbox_obj, created = Inbox.objects.using("erpro").get_or_create(
            inbox_id=msg_data.get("message_id"),
            defaults={
                "inbox_id": msg_data.get("message_id"),
                "message": text,
                "message_type": msg_data.get("message_type"),
                "inbox_by": sender,
                "inbox_date": timezone.now(),
                "is_processed": False,
                "data": msg_data.get("raw"),
                "session_id": device_id,
                "created": timezone.now(),
                "modified": timezone.now(),
                "properties": {},
                "description": None,
                "status": "draft",
            },
        )

        if created:
            # Standalone = proses langsung ke task sinkron
            if settings.STANDALONE:
                process(inbox_obj)

            # Menggunakan AI Agent
            elif settings.AI_AGENT:
                ai_reply(sender, msg_data, device_id)

            # Normal fallback
            else:
                async_fallback_reply(sender, msg_data, device_id)

    except Exception as e:
        logger.exception("Error processing inbox: %s", e)
        return None