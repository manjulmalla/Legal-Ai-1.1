from django.urls import path
from .views import explorer
from . import views

urlpatterns = [
    path('', explorer, name='explorer'),
    path('pdfs/', views.pdf_list, name='pdf_list'),
]
