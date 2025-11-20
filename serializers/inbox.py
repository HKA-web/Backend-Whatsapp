from rest_framework import serializers
from whatsapp.models.inbox import Inbox


class InboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inbox
        fields = [
            'inbox_id',
            'message',
            'message_type',
            'inbox_by',
            'inbox_date',
            'is_processed',
            'data',
            'session_id',
            'created',
            'modified',
            'is_removed',
            'read_only',
            'enable',
            'properties',
            'description',
            'status',
        ]
        
