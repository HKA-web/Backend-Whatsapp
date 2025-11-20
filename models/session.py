from django.db import models
from django.apps import apps
from django.utils import timezone

app_config = apps.get_containing_app_config(__name__)


class Session(models.Model):
    session_id = models.CharField(
        max_length=25,
        primary_key=True,
    )
    session_name = models.CharField(
        max_length=255,
    )
    data = models.JSONField(
        default=dict,
    )
    premised = models.BooleanField(
        default=True,
    )
    server = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=100,
		default='draft'
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        auto_now=True,
    )
    is_removed = models.BooleanField(default=False)
    read_only = models.BooleanField(default=False)
    enable = models.BooleanField(default=False)

    properties = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = u'"{}"."{}"'.format(app_config.label, 'session')
