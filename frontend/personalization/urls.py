from django.urls import path
from .views import personalization, save_preferences

urlpatterns = [
    path('', personalization, name='personalization'),
    path('save/', save_preferences, name='save_preferences'),
]