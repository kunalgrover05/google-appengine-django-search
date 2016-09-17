from django.conf.urls import url
from .views import search_service

urlpatterns = [
    url(r'^', search_service)
]
