import logging
from whatsapp.models.inbox import Inbox
from django.utils import timezone

logger = logging.getLogger('wa_command')

def process_inbox(inbox):
    try:
        from whatsapp.tasks import async_fallback_reply, process

        sender = inbox['inbox_by']
        msg_data = inbox['data']
        
        text = msg_data.get('text', '').strip()
        device_id = msg_data.get("bot_device", {}).get("phone")
        message_id = msg_data.get('message_id')

        if not message_id:
            logger.warning("Inbox data tidak memiliki message_id")
            return None

        inbox_obj, created = Inbox.objects.using('erpro').get_or_create(
            inbox_id=message_id,
            defaults={
                "inbox_id": message_id,
                "message": text,
                "message_type": msg_data.get('message_type'),
                "inbox_by": sender,
                "inbox_date": timezone.now(),
                "is_processed": False,
                "data": msg_data.get('raw'),
                "session_id": device_id,
                "created": timezone.now(),
                "modified": timezone.now(),
                "properties": {},
                "description": None,
                "status": 'draft',
            }
        )

        if created:
            # ===== RULES =====
            if text.lower() == 'hai':
                return '✅ Hai, Dikirim dengan backend.'

            # fallback reply bisa diaktifkan jika perlu
            # async_fallback_reply(sender, msg_data, device_id)

            # proses inbox baru
            process(inbox_obj)

        return None

    except Exception as e:
        logger.exception("Error saat memproses inbox: %s", e)
        return None
