from django.urls import path
from .views import dashboard, admin_conversations

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('api/conversations/', admin_conversations, name='admin_conversations'),
]
