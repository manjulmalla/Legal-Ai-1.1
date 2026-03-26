from django.urls import path
from .views import chat, send_message, get_conversations, get_conversation_history

urlpatterns = [
    path('', chat, name='chat'),
    path('api/message/', send_message, name='send_message'),
    path('api/conversations/', get_conversations, name='get_conversations'),
    path('api/conversations/<str:conversation_id>/', get_conversation_history, name='get_conversation_history'),
]