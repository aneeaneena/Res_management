from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.security_dashboard, name='delivery_dashboard'),
]

