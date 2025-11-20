from rest_framework import serializers
from whatsapp.models.sent import Sent


class SentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sent
        fields = [
            'sent_id',
            'message',
            'message_type',
            'sent_for',
            'sent_date',
            'prepare_date',
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
        
