from rest_framework import routers
from django.urls import path, include

router = routers.DefaultRouter()

urlpatterns = [
    path("api/", include(router.urls)),
]