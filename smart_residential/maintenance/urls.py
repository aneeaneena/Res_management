from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='maintenance_dashboard'),
    path('update-task/<int:task_id>/', views.update_task, name='update_task'),
]

