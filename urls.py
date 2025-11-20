from rest_framework import routers
from django.urls import path, include
from whatsapp.views.outbox import OutboxViewSet
from whatsapp.views.inbox import InboxViewSet
from whatsapp.views.sent import SentViewSet
from whatsapp.views.command import CommandViewSet, CommandActiveViewSet
from whatsapp.views.session import SessionViewSet

router = routers.DefaultRouter()
router.register(r'outbox', OutboxViewSet, basename='outbox')
router.register(r'inbox', InboxViewSet, basename='inbox')
router.register(r'sent', SentViewSet, basename='sent')
router.register(r'command', CommandViewSet, basename='command')
router.register(r'commandactive', CommandActiveViewSet, basename='commandactive')
router.register(r'session', SessionViewSet, basename='session')

urlpatterns = [
    path('api/', include(router.urls)),
]