import json
import logging
from datetime import datetime
from django.conf import settings
from huey.contrib.djhuey import task, periodic_task
from huey import crontab
from whatsapp.commands import process_inbox
from whatsapp.models.outbox import Outbox
from whatsapp.models.inbox import Inbox
from whatsapp.models.sent import Sent
from django.utils import timezone
import requests
import re as regex
from django.utils.translation import gettext_lazy as _
from utils.sslinogre import *
from pathlib import Path
import yaml
from whatsapp.utils import *

logger = logging.getLogger('wa_tasks')


# ======================================================
# QUEUE: SEND REPLY (RETRY SAFE)
# ======================================================
@task()
def queue_send_reply(sender, message, device_id, outbox_id=None):
    """
    Worker task untuk mengirim balasan WA.
    Retry max 3x via Outbox.retry.
    Anti-spam & aman dari error DB/parsing.
    """
    if settings.STANDALONE is False:
        # Mode langsung POST ke Node.js
        payload = {
            "jid": sender,
            "message": message,
            "_botDevice": device_id,
        }

        url = settings.NODE_API_URL
        if device_id:
            url = f"{url}?device={device_id}"

        try:
            res = requests.post(url, json=payload, timeout=20)
        except Exception as e:
            logger.error(f"❌ POST ke Node.js gagal: {e}")
            return

    else:
        # Mode simpan ke Outbox lokal
        # Default metadata
        prepare_date = timezone.now()
        session_id = device_id
        properties = {}
        retry = 0
        scheduled = False
        scheduled_date = None
        is_interactive = False
        is_answered = False
        answered_date = None
        data = {}

        # ======================================================
        # LOAD OUTBOX (JIKA ADA)
        # ======================================================
        outbox = None
        if outbox_id:
            try:
                outbox = Outbox.objects.using('erpro').get(pk=outbox_id)
                prepare_date = outbox.created
                session_id = outbox.session_id
                properties = outbox.properties or {}
                retry = outbox.retry or 0
                scheduled = outbox.scheduled or False
                scheduled_date = outbox.scheduled_date
                is_interactive = outbox.is_interactive
                is_answered = outbox.is_answered
                answered_date = outbox.answered_date
                data = outbox.data or {}
            except Exception as e:
                logger.error(f"⚠ Tidak bisa load Outbox {outbox_id}: {e}")

        payload = {
            "jid": sender,
            "message": message,
            "_botDevice": device_id,
        }

        url = settings.NODE_API_URL
        if device_id:
            url = f"{url}?device={device_id}"

        # ======================================================
        # STAGE 1 — POST KE NODE.JS → jika gagal: update retry
        # ======================================================
        try:
            res = requests.post(url, json=payload, timeout=20)
        except Exception as e:
            logger.error(f"❌ POST ke Node.js gagal: {e}")
            if outbox:
                outbox.data = outbox.data or {}
                outbox.data["traceback"] = str(e)
                outbox.modified = timezone.now()
                outbox.retry = retry + 1
                outbox.save(update_fields=["data", "retry", "modified"])
            return

        if res.status_code != 200:
            logger.warning(f"⚠ Node.js status {res.status_code}: {res.text}")
            if outbox:
                outbox.data = outbox.data or {}
                outbox.data["traceback"] = res.text
                outbox.modified = timezone.now()
                outbox.retry = retry + 1
                outbox.save(update_fields=["data", "retry", "modified"])
            return

        # ======================================================
        # STAGE 2 — Node.js SUKSES
        # ======================================================
        try:
            response = res.json()
            results = response.get("results", [])

            _sent_date = timezone.now()
            _answered_date = answered_date or timezone.now()
            _props = properties or {}
            _data = data or {}

            internal_errors = []

            for r in results:
                status = r.get("status")
                if status == "error":
                    internal_errors.append(r.get("error") or "Unknown error")
                    continue

                message_id = r.get("message_id")
                if not message_id:
                    internal_errors.append("Node.js tidak mengirim message_id")
                    continue

                # Aman: get_or_create → anti spam
                Sent.objects.using("erpro").get_or_create(
                    sent_id=message_id,
                    defaults={
                        "sent_id": message_id,
                        "message": message,
                        "message_type": "conversation",
                        "sent_for": sender,
                        "sent_date": _sent_date,
                        "prepare_date": prepare_date,
                        "retry": retry,
                        "scheduled": scheduled,
                        "scheduled_date": scheduled_date,
                        "is_interactive": is_interactive,
                        "is_answered": is_answered,
                        "answered_date": _answered_date,
                        "data": _data,
                        "session_id": session_id,
                        "created": timezone.now(),
                        "modified": timezone.now(),
                        "is_removed": False,
                        "read_only": False,
                        "enable": True,
                        "properties": _props,
                        "description": None,
                        "status": "sent",
                    }
                )

            # Jika ada error internal → update retry Outbox
            if internal_errors and outbox:
                outbox.data = outbox.data or {}
                outbox.data["traceback"] = internal_errors
                outbox.modified = timezone.now()
                outbox.retry = retry + 1
                outbox.save(update_fields=["data", "retry", "modified"])
                logger.error(f"⚠ Error internal Node.js: {internal_errors}")
                return

            # Semua sukses → hapus outbox
            if outbox:
                try:
                    outbox.delete(using='erpro')
                    logger.info(f"🗑 Outbox {outbox.outbox_id} dihapus (success).")
                except Exception as e:
                    logger.error(f"⚠ Gagal menghapus Outbox {outbox.outbox_id}: {e}")

            logger.info(f"✔ WA terkirim → {sender} (device={device_id or 'default'})")

        except Exception as e:
            logger.error(f"⚠ WA terkirim tapi gagal simpan DB/parsing: {e}")
            if outbox:
                outbox.data = outbox.data or {}
                outbox.data["traceback"] = str(e)
                outbox.modified = timezone.now()
                outbox.retry = retry + 1
                outbox.save(update_fields=["data", "retry", "modified"])
            return


# ======================================================
# HANDLE INCOMING MESSAGE
# ======================================================
@task(retries=3, retry_delay=5)
def handle_incoming_message(data):
    try:
        sender = data.get('sender') or data.get('key', {}).get('remoteJid')
        device_id = data.get('bot_device', {}).get('phone')

        inbox = {
            'id': int(datetime.now().timestamp()),
            'inbox_by': sender,
            'data': data
        }

        reply = process_inbox(inbox)
        if reply:
            queue_send_reply(sender, reply, device_id)

    except Exception as e:
        logger.exception(e)


# ======================================================
# FALLBACK AI
# ======================================================
@task(retries=2, retry_delay=3)
def ai_reply(sender, data, device_id):
    text = data.get('text', '').strip()

    FALLBACK_URL = settings.AI_AGENT_URL

    payload = {'query': {'user_id': sender, 'message': text}}

    try:
        res = requests.post(FALLBACK_URL, json=payload, timeout=30)
        if res.status_code != 200:
            return queue_send_reply(sender, '❌ Tidak dapat memproses permintaan', device_id)

        result = res.json()
        msg = (result[0].get('message', '') if isinstance(result, list) else '').strip()
        if not msg:
            msg = '❌ Tidak ada respon dari AI'

        queue_send_reply(sender, msg, device_id)

    except Exception as e:
        logger.exception(f'AI Agent error: {e}')
        queue_send_reply(sender, '❌ Permintaan gagal', device_id)


# ======================================================
# FALLBACK
# ======================================================
@task(retries=2, retry_delay=3)
def async_fallback_reply(sender, data, device_id):
    try:
        # ambil token access terbaru dari config.yaml
        token = LoadWebhookAuth()

        body = [{
            "message": "Hai hakim",
            "message_type": "conversation",
            "outbox_for": "6285648007953@s.whatsapp.net",
            "is_interactive": False,
            "session": f"{device_id}",
            "properties": {"id": "-"},
            "description": ""
        }]

        # 1) Send normal
        res = SendMessage(token, body)

        if res.get("success"):
            return True

        # 2) Refresh token
        if Refresh():
            new_token = LoadWebhookAuth()
            res2 = SendMessage(new_token, body)

            if res2.get("success"):
                return True

        # 3) Auth ulang
        if Auth():
            fresh_token = LoadWebhookAuth()
            res3 = SendMessage(fresh_token, body)

            if res3.get("success"):
                return True

        # 4) Semua gagal
        queue_send_reply(sender, "❌ Gagal mengirim pesan ke server", device_id)
        return False

    except Exception as e:
        queue_send_reply(sender, f"❌ Error sistem: {e}", device_id)
        return False


# ======================================================
# PERIODIC TASK: PROCESS OUTBOX
# ======================================================
@periodic_task(crontab(minute='*'))
def outbox_process():
    # Jika bukan mode STANDALONE → langsung keluar, jangan collect Outbox
    # if not settings.STANDALONE:
        # return

    # Mode standalone → baru collect Outbox
    outbox_list = Outbox.objects.using('erpro').filter(
        message_type='conversation',
        retry__lt=settings.RETRY
    )

    for outbox in outbox_list:
        try:
            queue_send_reply(
                outbox.outbox_for,
                outbox.message,
                outbox.session_id,
                outbox.pk
            )
        except Exception as e:
            logger.exception(f'Outbox push error: {e}')
			
			
def prepare(inbox: Inbox):
    from whatsapp.models.command import Command, CommandActive

    command_active = None

    def check(command: inbox.command):
        searchs = Command.objects.using('erpro').filter(
            session_id=inbox.session_id,
            command__iexact=command,
            enable=True,
        )

        if not searchs.exists():
            searchs = Command.objects.using('erpro').filter(
                session_id=inbox.session_id,
                command__iexact='/'.join(command.split()),
                enable=True,
            )

        if searchs.exists():
            return searchs

        next_cmd = ' '.join(command.split()[0:len(command.split()) - 1])
        if next_cmd:
            return check(next_cmd.strip())

        return None

    commands = check(
        ' '.join(regex.split(r'\W+', inbox.command.strip()))
    ) if inbox.command else None

    if commands and commands.exists():
        for command in commands:
            if inbox.command.strip().lower() not in (
                command.command.strip().lower(),
            ):
                parameters = inbox.command.strip()[len(command.command.strip()):].split()
                for index, item in enumerate(command.required_parameter):
                    if index < len(parameters):
                        parameters[index] = f'{item}={parameters[index]}'

                inbox.refresh_from_db(fields=['data'])
                inbox.message = (
                    f"{inbox.command.strip()[:len(command.command.strip())].strip().lower()}\n"
                    f"{'\n'.join(parameters)}\n"
                    f"parameters={inbox.command.strip()[len(command.command.strip()):]}"
                )

            command_active = CommandActive.objects.using('erpro').create(
                command_id=command.pk,
                command_by=inbox.inbox_by,
                parameter=inbox.parameter,
                enable=True,
            )

    else:
        for active in CommandActive.objects.using('erpro').filter(
            command__session_id=inbox.session_id,
            command_by=inbox.inbox_by,
            enable=True,
        ):
            merged = f"{active.command.command}/{inbox.command}".strip()
            commands = check(' '.join(regex.split(r'\W+', merged)))

            for command in commands:
                if merged.lower() not in (
                    command.command.strip().lower(),
                ):
                    parameters = merged[len(command.command.strip()):].split()
                    for index, item in enumerate(command.required_parameter):
                        if index < len(parameters):
                            parameters[index] = f"{item}={parameters[index]}"

                    inbox.refresh_from_db(fields=['data'])
                    inbox.message = (
                        f"{merged[:len(command.command.strip())].strip().lower()}\n"
                        f"{'\n'.join(parameters)}\n"
                        f"parameters={merged[len(command.command.strip()):]}"
                    )

                command_active = CommandActive.objects.using('erpro').create(
                    command_id=command.pk,
                    command_by=inbox.inbox_by,
                    parameter=inbox.parameter,
                    enable=True,
                )

    # --- FIXED INDENTATION: blok ini harus sejajar dengan blok `if commands...`
    if command_active:
        required_parameter = (
            command_active.command.required_parameter
            if command_active.command.mirror is None
            else command_active.command.mirror.required_parameter
        )

        check_parameter = (
            command_active.command.check_parameter
            if command_active.command.mirror is None
            else command_active.command.mirror.check_parameter
        )

        if (
            not all(
                parameter in command_active.parameter
                for parameter in (required_parameter or [])
            )
            and check_parameter
        ):
            Outbox.objects.using('erpro').create(
                message=_('Parameter \n%(parameter)s \nIs Required')
                % dict(parameter='\n'.join(required_parameter)),
                message_type='conversation',
                outbox_for=inbox.inbox_by,
                session_id=inbox.session_id,
                enable=True,
                properties=dict(command=command_active.command.pk),
            )
            return None

    else:
        command, created = Command.objects.using('erpro').get_or_create(
            pk=f"WhatsApp.{inbox.message_type}",
            defaults=dict(
                command_id=f"WhatsApp.{inbox.message_type}",
                command_name=f"WhatsApp {inbox.message_type}",
                command=f"whatsapp/{inbox.message_type}".lower(),
                command_type=Command.Type.TXT,
                process=[],
                enable=False,
                is_finish=True,
                required_parameter=[],
                required_permission=[],
                session_id=inbox.session_id,
                description=_(
                    "<p>Exclusive command whatsapp/%(message_type)s By WhatsApp, "
                    "Use this command for any type of Inbox message that doesn't match your Command</p>"
                )
                % dict(message_type=inbox.message_type.lower()),
            ),
        )

        command_active = CommandActive.objects.using('erpro').create(
            command_id=command.pk,
            command_by=inbox.inbox_by,
            parameter=inbox.parameter,
        )

        if not command.enable:
            return None

    return command_active

			
@task()
def process(inbox: Inbox):
    if inbox:
        from whatsapp.models.command import Command
        command_active = prepare(inbox)

        if command_active:
            processes = (
                command_active.command.process
                if command_active.command.mirror is None
                else command_active.command.mirror.process
            )

            for process in processes:
                logger.info(
                    f"Execute command {command_active.command.command} "
                    f"{command_active.command.command_type}"
                )

                # ======================== TXT ========================
                if command_active.command.command_type in (Command.Type.TXT,):
                    Outbox.objects.using('erpro').create(
                        message=process.format(
                            environment=namedtuple(
                                'Environment',
                                os.environ.keys(),
                                rename=True,
                            )(*os.environ.values()),
                            setting=djangosettings,
                            now=timezone.now(),
                            inbox=inbox,
                            command_active=command_active,
                        ),
                        message_type='chat',
                        outbox_for=inbox.inbox_by,
                        session=inbox.session,
                        enable=True,
                        properties=dict(command=command_active.command.pk),
                    )

                # ======================== SQL ========================
                if command_active.command.command_type in (Command.Type.SQL,):
                    from django.template import Context, Template
                    from django.db import connection

                    query = Template(process).render(
                        Context(
                            dict(
                                inbox=inbox,
                                command_active=command_active,
                            )
                        )
                    )

                    cursor = connection.cursor()
                    cursor.execute(query)
                    connection.commit()

                # ========================= PY ========================
                if command_active.command.command_type in (Command.Type.PY,):
                    result = dict()
                    formatted = '\n\t'.join(process.strip().splitlines())

                    exec(
                        f"def function():\n\t{formatted}",
                        dict(
                            inbox=inbox,
                            command_active=command_active,
                        ),
                        result,
                    )

                    function = result[list(result)[-1]]
                    function()

            # ===================== FINISH =====================
            if command_active.command.is_finish:
                command_active.refresh_from_db()
                command_active.delete(soft=False)

        else:
            if inbox.message_type in ('chat', 'image', 'video') and inbox.command:
                pass

        inbox.is_processed = True
        inbox.save()


