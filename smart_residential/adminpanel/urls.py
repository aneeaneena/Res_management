from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='admin_dashboard'),
    path('approve/', views.approve_residents, name='approve_residents'),
    path('notices/', views.manage_notices, name='manage_notices'),
    path('deliveries/', views.manage_deliveries, name='manage_deliveries'),
    path('maintenance/', views.assign_maintenance, name='assign_maintenance'),
    path('amenities/', views.manage_amenities, name='manage_amenities'),
]

