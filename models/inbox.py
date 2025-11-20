from django.db import models
from django.apps import apps
from django.utils.translation import gettext_lazy as _
from whatsapp.models.session import Session
from whatsapp.utils import strings

app_config = apps.get_containing_app_config(__name__)


class Inbox(models.Model):
    inbox_id = models.CharField(
        max_length=100,
        primary_key=True,
    )
    message = models.TextField(
        blank=True,
        null=True,
    )
    message_type = models.CharField(
        max_length=100,
    )
    inbox_by = models.CharField(
        max_length=255,
    )
    inbox_date = models.DateTimeField(
        blank=True,
        null=True,
    )
    is_processed = models.BooleanField(
        default=False,
    )
    data = models.JSONField(
        default=dict,
    )
    session = models.ForeignKey(
        to=Session,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    created = models.DateTimeField()
    modified = models.DateTimeField()
    is_removed = models.BooleanField(default=False)
    read_only = models.BooleanField(default=False)
    enable = models.BooleanField(default=False)
    properties = models.JSONField(
        default=dict,
        blank=True,
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
		default='draft'
    )

    @property
    def command(self):
        if self.message:
            lines = self.message.splitlines()
            return lines[0] if len(lines) > 0 else None
        return None

    @property
    def parameter(self):
        parameter = {}
        if self.command:
            parameter = strings.stringproperties(self.message)
        return parameter

    class Meta:
        managed = False
        db_table = '"{}"."{}"'.format(app_config.label, 'inbox')

