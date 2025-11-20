from rest_framework import viewsets

from whatsapp.models.sent import Sent
from whatsapp.serializers.sent import SentSerializer


class SentViewSet(viewsets.ModelViewSet):
    serializer_class = SentSerializer
    database_name = 'erpro'

    def get_queryset(self):
        return Sent.objects.using(self.database_name).all()[:25]

    def perform_create(self, serializer):
        serializer.save(using=self.database_name)

    def perform_update(self, serializer):
        serializer.save(using=self.database_name)

    def perform_destroy(self, instance):
        instance.delete(using=self.database_name)
