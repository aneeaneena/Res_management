from django.contrib import admin

from .models import (
    ResidentProfile,
    MaintenanceRequest,
    AmenityBooking,
    Amenity,
    DeliveryItem,
    ResidentNotice,
    SupportMessage,
)

admin.site.register(ResidentProfile)
admin.site.register(MaintenanceRequest)
admin.site.register(AmenityBooking)
admin.site.register(DeliveryItem)
admin.site.register(ResidentNotice)
admin.site.register(Amenity)
admin.site.register(SupportMessage)
