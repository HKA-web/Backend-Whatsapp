from django.db import models
from django.apps import apps

app_config = apps.get_containing_app_config(__name__)

class Sent(models.Model):
    sent_id = models.CharField(max_length=255, primary_key=True)
    message = models.CharField(max_length=255)
    message_type = models.CharField(max_length=255)
    sent_for = models.CharField(max_length=255)
    sent_date = models.DateTimeField()
    prepare_date = models.DateTimeField()
    retry = models.IntegerField(default=0)
    scheduled = models.BooleanField(default=False)
    scheduled_date = models.DateTimeField()
    is_interactive = models.BooleanField(default=False)
    is_answered = models.BooleanField(default=False)
    answered_date = models.DateTimeField()
    data = models.JSONField()
    session_id = models.CharField(max_length=255)
    template_id = None
    created = models.DateTimeField()
    modified = models.DateTimeField()
    is_removed = models.BooleanField(default=False)
    read_only = models.BooleanField(default=False)
    enable = models.BooleanField(default=False)
    properties = models.JSONField()
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = u'\"{}\".\"{}\"'.format(app_config.label, 'sent')