from django.db import models

from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    ROLE_CHOICES = (
        ('resident', 'Resident'),
        ('delivery', 'Delivery Staff'),
        ('maintenance', 'Maintenance Staff'),
        ('admin', 'Admin'),
    )
    DELIVERY_TYPE_CHOICES = (
        ('milk', 'Milk'),
        ('water', 'Water'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_TYPE_CHOICES, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True)
    profile_picture = models.FileField(upload_to="profile_pics/", blank=True, null=True)
    application_document = models.FileField(upload_to="application_docs/", blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Create your models here.
