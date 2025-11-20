from rest_framework import viewsets

from whatsapp.models.inbox import Inbox
from whatsapp.serializers.inbox import InboxSerializer


class InboxViewSet(viewsets.ModelViewSet):
    serializer_class = InboxSerializer
    database_name = 'erpro'

    def get_queryset(self):
        return Inbox.objects.using(self.database_name).all()[:25]

    def perform_create(self, serializer):
        serializer.save(using=self.database_name)

    def perform_update(self, serializer):
        serializer.save(using=self.database_name)

    def perform_destroy(self, instance):
        instance.delete(using=self.database_name)
