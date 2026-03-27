from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ResidentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="resident_profile")
    unit = models.CharField(max_length=20, blank=True)
    building = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)
    profile_picture = models.FileField(upload_to="profile_pics/", blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True)
    emergency_name = models.CharField(max_length=120, blank=True)
    emergency_phone = models.CharField(max_length=30, blank=True)
    lease_file = models.FileField(upload_to="leases/", blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.unit or 'No Unit'})"


class MaintenanceRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("on_hold", "On Hold"),
    )
    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    )

    resident = models.ForeignKey(User, on_delete=models.CASCADE, related_name="maintenance_requests")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_maintenance_requests",
    )
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    due_date = models.DateTimeField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    technician_comments = models.TextField(blank=True)
    completion_otp = models.CharField(max_length=6, blank=True)
    otp_verified_at = models.DateTimeField(blank=True, null=True)
    evidence_file = models.FileField(upload_to="maintenance_evidence/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class AmenityBooking(models.Model):
    STATUS_CHOICES = (
        ("booked", "Booked"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    resident = models.ForeignKey(User, on_delete=models.CASCADE, related_name="amenity_bookings")
    amenity = models.ForeignKey(
        "Amenity", on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings"
    )
    amenity_name = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="booked")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.amenity.name if self.amenity else self.amenity_name
        return f"{name} ({self.status})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["amenity", "start_time"], name="uniq_amenity_slot"),
        ]


class Amenity(models.Model):
    CATEGORY_CHOICES = (
        ("fitness", "Fitness"),
        ("leisure", "Leisure"),
        ("social", "Social"),
    )

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="social")
    open_time = models.TimeField()
    close_time = models.TimeField()
    slot_minutes = models.PositiveIntegerField(default=60)
    image_url = models.URLField(blank=True)

    def __str__(self):
        return self.name


class DeliveryItem(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("ready", "Ready"),
        ("picked_up", "Picked Up"),
        ("delivered", "Delivered"),
        ("skipped", "Skipped"),
    )
    PAYMENT_METHOD_CHOICES = (
        ("na", "N/A"),
        ("online", "Online"),
        ("at_delivery", "Pay at Delivery"),
    )
    PAYMENT_STATUS_CHOICES = (
        ("na", "N/A"),
        ("pending", "Pending"),
        ("paid", "Paid"),
    )

    resident = models.ForeignKey(User, on_delete=models.CASCADE, related_name="delivery_items")
    carrier = models.CharField(max_length=60)
    label = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="na")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="na")
    payment_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payment_reference = models.CharField(max_length=80, blank=True)
    delivery_otp = models.CharField(max_length=6, blank=True)
    otp_verified_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.carrier} - {self.label}"


class ResidentNotice(models.Model):
    PRIORITY_CHOICES = (
        ("normal", "Normal"),
        ("important", "Important"),
        ("urgent", "Urgent"),
    )

    title = models.CharField(max_length=200)
    body = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="normal")
    publish_from = models.DateTimeField(default=timezone.now)
    publish_until = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class SupportMessage(models.Model):
    resident = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_messages")
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resident.username} - {self.subject}"
