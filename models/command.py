from django.db import models
from django.apps import apps
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _
from enum import auto
from strenum import LowercaseStrEnum
from whatsapp.models.session import Session

app_config = apps.get_containing_app_config(__name__)


class Command(models.Model):

    class Type(LowercaseStrEnum):
        TXT = auto()
        SQL = auto()
        PY = auto()

    CommandType = [
        (Type.TXT, _('Command Text')),
        (Type.SQL, _('Command Query SQL')),
        (Type.PY, _('Command Python Script')),
    ]

    command_id = models.CharField(
        primary_key=True,
        max_length=255,
    )
    command_name = models.CharField(max_length=255)
    command = models.CharField(max_length=255)

    mirror = models.ForeignKey(
        to='self',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='children_set',
    )

    command_type = models.CharField(
        max_length=50,
        choices=CommandType,
    )

    process = ArrayField(
        base_field=models.TextField(),
        blank=True,
    )

    required_parameter = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        null=True,
    )

    check_parameter = models.BooleanField(default=True)

    required_permission = ArrayField(
        base_field=models.BigIntegerField(),
        blank=True,
        null=True,
    )

    check_permission = models.BooleanField(default=False)
    is_finish = models.BooleanField(default=False)

    session = models.ForeignKey(
        to=Session,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    is_removed = models.BooleanField(default=False)
    read_only = models.BooleanField(default=False)
    enable = models.BooleanField(default=False)

    properties = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True, default='draft')

    class Meta:
        managed = False
        db_table = u'"{}"."{}"'.format(app_config.label, 'command')

    @property
    def has_children(self):
        return self.children_set.count() > 0


class CommandActive(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=255,
    )

    command = models.ForeignKey(
        to=Command,
        on_delete=models.CASCADE,
    )

    previous_command = models.ForeignKey(
        to=Command,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='previous_set',
    )

    parameter = models.JSONField(default=dict)

    command_by = models.CharField(max_length=255)

    command_date = models.DateTimeField(
        blank=True,
        null=True,
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    is_removed = models.BooleanField(default=False)
    read_only = models.BooleanField(default=False)
    enable = models.BooleanField(default=False)

    properties = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = u'"{}"."{}"'.format(app_config.label, 'command_active')
