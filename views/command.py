from rest_framework import viewsets

from whatsapp.models.command import Command, CommandActive
from whatsapp.serializers.command import CommandSerializer, CommandActiveSerializer


class CommandViewSet(viewsets.ModelViewSet):
    serializer_class = CommandSerializer
    database_name = 'erpro'

    def get_queryset(self):
        return Command.objects.using(self.database_name).all()

    def perform_create(self, serializer):
        serializer.save(using=self.database_name)

    def perform_update(self, serializer):
        serializer.save(using=self.database_name)

    def perform_destroy(self, instance):
        instance.delete(using=self.database_name)


class CommandActiveViewSet(viewsets.ModelViewSet):
    serializer_class = CommandActiveSerializer
    database_name = 'erpro'

    def get_queryset(self):
        return CommandActive.objects.using(self.database_name).all()

    def perform_create(self, serializer):
        serializer.save(using=self.database_name)

    def perform_update(self, serializer):
        serializer.save(using=self.database_name)

    def perform_destroy(self, instance):
        instance.delete(using=self.database_name)
