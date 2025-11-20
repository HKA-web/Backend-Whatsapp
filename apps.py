from django.apps import AppConfig
import threading
import logging
import os


class WhatsappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "whatsapp"

    def ready(self):
        """
        Dipanggil otomatis saat Django startup.
        Hanya jalan sekali (hindari duplikasi akibat autoreload).
        """
        if os.environ.get("RUN_MAIN") != "true":
            return

        try:
            from whatsapp.listener import start_listener

            # Jalankan listener di thread terpisah
            threading.Thread(target=start_listener, daemon=True).start()

            logging.getLogger("wa_listener").info(
                "🚀 Redis listener started via AppConfig.ready()"
            )

        except Exception as e:
            logging.getLogger("wa_listener").exception(
                f"❌ Gagal menjalankan Redis listener: {e}"
            )
