from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from resident.models import (
    ResidentProfile,
    MaintenanceRequest,
    AmenityBooking,
    DeliveryItem,
    ResidentNotice,
    Amenity,
)


class Command(BaseCommand):
    help = "Seed sample resident data for testing."

    def handle(self, *args, **options):
        now = timezone.now()

        users = []
        for username in ["resident1", "resident2"]:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password("password123")
                user.email = f"{username}@example.com"
                user.save()
            users.append(user)

        for idx, user in enumerate(users, start=1):
            ResidentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "unit": f"{200 + idx}",
                    "building": "Building A",
                    "avatar_url": "",
                },
            )

        amenities = [
            {
                "name": "Elite Fitness Center",
                "description": "Fully equipped fitness center with premium cardio machines, free weights, and dedicated stretching zones.",
                "category": "fitness",
                "open_time": "00:00",
                "close_time": "23:59",
                "slot_minutes": 60,
                "image_url": "",
            },
            {
                "name": "Heated Olympic Pool",
                "description": "Crystal clear heated pool perfect for laps or relaxation.",
                "category": "leisure",
                "open_time": "06:00",
                "close_time": "22:00",
                "slot_minutes": 60,
                "image_url": "",
            },
            {
                "name": "Community Grand Hall",
                "description": "Spacious multi-purpose hall for celebrations and meetings.",
                "category": "social",
                "open_time": "08:00",
                "close_time": "21:00",
                "slot_minutes": 60,
                "image_url": "",
            },
        ]
        amenity_objs = []
        for a in amenities:
            amenity, _ = Amenity.objects.get_or_create(
                name=a["name"],
                defaults={
                    "description": a["description"],
                    "category": a["category"],
                    "open_time": a["open_time"],
                    "close_time": a["close_time"],
                    "slot_minutes": a["slot_minutes"],
                    "image_url": a["image_url"],
                },
            )
            amenity_objs.append(amenity)

        for user in users:
            MaintenanceRequest.objects.get_or_create(
                resident=user,
                title="Leaking Sink",
                defaults={
                    "description": "Slow drip under the kitchen sink.",
                    "status": "in_progress",
                },
            )

            start_time = now + timedelta(days=1, hours=2 + users.index(user))
            end_time = start_time + timedelta(hours=1)
            AmenityBooking.objects.get_or_create(
                amenity=amenity_objs[0],
                start_time=start_time,
                defaults={
                    "resident": user,
                    "amenity_name": amenity_objs[0].name,
                    "status": "booked",
                    "end_time": end_time,
                },
            )

            DeliveryItem.objects.get_or_create(
                resident=user,
                carrier="Resident Booking",
                label="Milk Delivery",
                defaults={
                    "status": "pending",
                    "delivered_at": None,
                },
            )

        ResidentNotice.objects.get_or_create(
            title="Elevator Maintenance",
            defaults={
                "body": "The service elevator will be down for maintenance this Friday 9 AM - 4 PM.",
                "priority": "important",
            },
        )
        ResidentNotice.objects.get_or_create(
            title="Community BBQ",
            defaults={
                "body": "Join us Saturday at 6 PM in the rooftop lounge for food and music.",
                "priority": "normal",
            },
        )

        self.stdout.write(self.style.SUCCESS("Seeded resident data."))
