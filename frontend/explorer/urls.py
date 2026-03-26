from django.urls import path
from .views import explorer

urlpatterns = [
    path('', explorer, name='explorer'),
]
