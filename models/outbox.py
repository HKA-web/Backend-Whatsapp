from django.db import models
from django.apps import apps
from django.utils import timezone

app_config = apps.get_containing_app_config(__name__)


class Outbox(models.Model):
    outbox_id = models.CharField(
        max_length=100,
        primary_key=True,
    )

    sent_id = models.CharField(
        max_length=100,
    )

    template_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    message = models.TextField(
        blank=True,
        null=True,
    )

    message_type = models.CharField(
        max_length=100,
    )

    outbox_for = models.CharField(
        max_length=100,
    )

    prepare_date = models.DateTimeField(
        default=timezone.now,
    )

    retry = models.IntegerField(
        default=0,
    )

    scheduled = models.BooleanField(
        default=False,
    )

    scheduled_date = models.DateTimeField(
        blank=True,
        null=True,
    )

    is_interactive = models.BooleanField(
        default=False,
    )

    is_answered = models.BooleanField(
        default=False,
    )

    answered_date = models.DateTimeField(
        blank=True,
        null=True,
    )

    data = models.JSONField(
        default=dict,
    )

    session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=100,
		default='draft'
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    modified = models.DateTimeField(
        auto_now=True
    )

    is_removed = models.BooleanField(default=False)
    read_only = models.BooleanField(default=False)
    enable = models.BooleanField(default=False)

    properties = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = u'"{}"."{}"'.format(app_config.label, 'outbox')
