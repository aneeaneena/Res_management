from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('resident/', include('resident.urls')),
    path('adminpanel/', include('adminpanel.urls')),
    path('maintenance/', include('maintenance.urls')),
    path('amenities/', include('amenities.urls')),
    path('delivery/', include('delivery.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
