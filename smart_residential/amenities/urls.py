from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_amenities),
    path('detail/', views.detail),
    path('book-slot/', views.book_slot),
    path('history/', views.history),
]
