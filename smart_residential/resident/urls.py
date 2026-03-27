from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='resident_dashboard'),   
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('book-delivery/', views.book_delivery, name='book_delivery'),
    path('maintenance/', views.maintenance_request, name='maintenance_request'),
    path('maintenance/evidence/<int:request_id>/', views.view_evidence, name='resident_view_evidence'),
    path('delivery-status/', views.delivery_status, name='delivery_status'),
    path('amenities/', views.amenities, name='amenities'),
    path('notices/', views.notices, name='notices'),
]

