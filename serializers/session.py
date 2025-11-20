from rest_framework import serializers
from whatsapp.models.session import Session


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = [
            'session_id',
            'session_name',
            'premised',
            'server',
            'data',
            'created',
            'modified',
            'read_only',
            'enable',
            'properties',
            'description',
        ]
        
