from django.urls import path
from . import views

urlpatterns = [
    path("voice/", views.voice_chat),
    path("chat/", views.chat),
    path("speak/", views.speak),
]