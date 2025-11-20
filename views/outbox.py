from rest_framework import viewsets

from whatsapp.models.outbox import Outbox
from whatsapp.serializers.outbox import OutboxSerializer


class OutboxViewSet(viewsets.ModelViewSet):
    serializer_class = OutboxSerializer
    database_name = 'erpro'

    def get_queryset(self):
        return Outbox.objects.using(self.database_name).filter(message_type='conversation')

    def perform_create(self, serializer):
        serializer.save(using=self.database_name)

    def perform_update(self, serializer):
        serializer.save(using=self.database_name)

    def perform_destroy(self, instance):
        instance.delete(using=self.database_name)
