from django.urls import path
from .views import index, search_questions


urlpatterns = [
    path('', index, name="home"),
    path('search/', search_questions, name="search_questions"),
]