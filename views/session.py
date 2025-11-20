from rest_framework import viewsets

from whatsapp.models.session import Session
from whatsapp.serializers.session import SessionSerializer


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = SessionSerializer
    database_name = 'erpro'

    def get_queryset(self):
        return Session.objects.using(self.database_name).all()

    def perform_create(self, serializer):
        serializer.save(using=self.database_name)

    def perform_update(self, serializer):
        serializer.save(using=self.database_name)

    def perform_destroy(self, instance):
        instance.delete(using=self.database_name)
