from rest_framework import serializers
from whatsapp.models.command import Command, CommandActive


class CommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Command
        fields = [
            'command_id',
            'command_name',
            'command',
            'mirror_id',
            'command_type',
            'process',
            'required_parameter',
            'check_parameter',
            'required_permission',
            'check_permission',
            'is_finish',
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
        
class CommandActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandActive
        fields = [
            'id',
            'command_id',
            'previous_command_id',
            'parameter',
            'command_by',
            'command_date',
            'created',
            'modified',
            'is_removed',
            'read_only',
            'enable',
            'properties',
            'description',
        ]
        
