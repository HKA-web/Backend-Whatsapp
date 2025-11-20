from rest_framework import serializers
from whatsapp.models.outbox import Outbox


class OutboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outbox
        fields = [
            'outbox_id',
            'message',
            'message_type',
            'outbox_for',
            'retry',
            'scheduled',
            'scheduled_date',
            'is_interactive',
            'is_answered',
            'answered_date',
            'data',
            'session_id',
            'template_id',
            'created',
            'modified',
            'is_removed',
            'read_only',
            'enable',
            'properties',
            'description',
            'status',
        ]
        
