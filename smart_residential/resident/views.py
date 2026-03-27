from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import IntegrityError
from decimal import Decimal, InvalidOperation
from urllib.parse import quote
from secrets import choice

from accounts.decorators import resident_only
from .models import (
    ResidentProfile,
    MaintenanceRequest,
    AmenityBooking,
    Amenity,
    DeliveryItem,
    ResidentNotice,
)

WATER_UPI_ID = "smartresidential@upi"
WATER_PAYEE_NAME = "Smart Residential"
WATER_DEFAULT_AMOUNT = Decimal("50.00")


def _get_resident_profile(user):
    try:
        return ResidentProfile.objects.get(user=user)
    except ResidentProfile.DoesNotExist:
        return None


def _missing_profile_fields(user, resident_profile):
    if resident_profile is None:
        return ["unit", "building", "phone", "emergency_name", "emergency_phone"]

    required_values = {
        "unit": resident_profile.unit,
        "building": resident_profile.building,
        "phone": resident_profile.phone,
        "emergency_name": resident_profile.emergency_name,
        "emergency_phone": resident_profile.emergency_phone,
        "email": user.email,
    }
    return [field for field, value in required_values.items() if not str(value or "").strip()]


def _redirect_if_profile_incomplete(request, resident_profile):
    if _missing_profile_fields(request.user, resident_profile):
        if request.path != reverse("profile"):
            return redirect("profile")
    return None


def _create_skip_deliveries(resident, start_date, skip_days, skip_milk, skip_newspaper, vendor):
    created = 0
    for offset in range(skip_days):
        service_date = start_date + timedelta(days=offset)
        if skip_milk:
            DeliveryItem.objects.create(
                resident=resident,
                carrier=vendor or "Resident Skip Request",
                label=f"Milk Delivery Skip ({service_date:%Y-%m-%d})",
                status="skipped",
                delivered_at=None,
            )
            created += 1
        if skip_newspaper:
            DeliveryItem.objects.create(
                resident=resident,
                carrier=vendor or "Resident Skip Request",
                label=f"Newspaper Delivery Skip ({service_date:%Y-%m-%d})",
                status="skipped",
                delivered_at=None,
            )
            created += 1
    return created


def _water_qr_url(amount):
    upi_uri = (
        f"upi://pay?pa={WATER_UPI_ID}&pn={WATER_PAYEE_NAME}"
        f"&am={amount:.2f}&cu=INR&tn=Water Booking"
    )
    return "https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=" + quote(upi_uri, safe="")


def _generate_delivery_otp():
    digits = "0123456789"
    return "".join(choice(digits) for _ in range(6))


def _generate_maintenance_otp():
    digits = "0123456789"
    return "".join(choice(digits) for _ in range(6))


@resident_only
def dashboard(request):
    resident_profile = _get_resident_profile(request.user)
    redirect_response = _redirect_if_profile_incomplete(request, resident_profile)
    if redirect_response:
        return redirect_response
    deliveries = DeliveryItem.objects.filter(resident=request.user).order_by("-created_at")[:3]
    pending_deliveries_count = DeliveryItem.objects.filter(
        resident=request.user, status__in=["pending", "ready"]
    ).count()
    active_requests_count = MaintenanceRequest.objects.filter(
        resident=request.user, status__in=["pending", "in_progress"]
    ).count()
    booked_amenities_count = AmenityBooking.objects.filter(
        resident=request.user, status="booked"
    ).count()
    notices = ResidentNotice.objects.order_by("-created_at")[:2]
    notices_count = ResidentNotice.objects.count()
    maintenance_requests = MaintenanceRequest.objects.filter(resident=request.user).order_by("-created_at")[:1]
    amenity_bookings = AmenityBooking.objects.filter(resident=request.user).order_by("-start_time")[:4]

    return render(request, "resident/dashboard.html", {
        "resident_profile": resident_profile,
        "deliveries": deliveries,
        "pending_deliveries_count": pending_deliveries_count,
        "active_requests_count": active_requests_count,
        "booked_amenities_count": booked_amenities_count,
        "notices": notices,
        "notices_count": notices_count,
        "maintenance_requests": maintenance_requests,
        "amenity_bookings": amenity_bookings,
    })

@resident_only
def profile(request):
    resident_profile = _get_resident_profile(request.user)
    if not resident_profile:
        resident_profile = ResidentProfile.objects.create(user=request.user)

    toast_success = None
    toast_error = None
    missing_fields = _missing_profile_fields(request.user, resident_profile)
    force_complete = bool(missing_fields)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_profile":
            email = request.POST.get("email", request.user.email).strip()
            unit = request.POST.get("unit", resident_profile.unit).strip()
            building = request.POST.get("building", resident_profile.building).strip()
            phone = request.POST.get("phone", resident_profile.phone).strip()
            emergency_name = request.POST.get("emergency_name", resident_profile.emergency_name).strip()
            emergency_phone = request.POST.get("emergency_phone", resident_profile.emergency_phone).strip()

            required_values = {
                "Email": email,
                "Unit": unit,
                "Building": building,
                "Phone": phone,
                "Emergency contact name": emergency_name,
                "Emergency contact phone": emergency_phone,
            }
            missing_labels = [label for label, value in required_values.items() if not value]
            if missing_labels:
                toast_error = f"Please complete all required fields: {', '.join(missing_labels)}."
                return render(request, "resident/profile.html", {
                    "resident_profile": resident_profile,
                    "toast_success": toast_success,
                    "toast_error": toast_error,
                    "force_complete": force_complete,
                    "missing_fields": missing_fields,
                })

            request.user.email = email
            request.user.save(update_fields=["email"])

            resident_profile.unit = unit
            resident_profile.building = building
            resident_profile.phone = phone
            resident_profile.emergency_name = emergency_name
            resident_profile.emergency_phone = emergency_phone
            resident_profile.save()
            missing_fields = _missing_profile_fields(request.user, resident_profile)
            force_complete = bool(missing_fields)
            toast_success = "Profile updated successfully." if not force_complete else "Profile updated. Please complete the remaining required fields."
        elif action == "upload_profile_picture":
            profile_picture = request.FILES.get("profile_picture")
            if not profile_picture:
                toast_error = "Please choose an image file."
            elif not str(profile_picture.content_type or "").startswith("image/"):
                toast_error = "Only image files are allowed for profile picture."
            else:
                resident_profile.profile_picture = profile_picture
                resident_profile.save(update_fields=["profile_picture"])
                toast_success = "Profile picture uploaded successfully."
        elif action == "upload_lease":
            if force_complete:
                toast_error = "Complete your profile details first."
                return render(request, "resident/profile.html", {
                    "resident_profile": resident_profile,
                    "toast_success": toast_success,
                    "toast_error": toast_error,
                    "force_complete": force_complete,
                    "missing_fields": missing_fields,
                })
            lease_file = request.FILES.get("lease_file")
            if lease_file:
                resident_profile.lease_file = lease_file
                resident_profile.save()
                toast_success = "Lease uploaded successfully."
            else:
                toast_error = "Please choose a file."

    return render(request, "resident/profile.html", {
        "resident_profile": resident_profile,
        "toast_success": toast_success,
        "toast_error": toast_error,
        "force_complete": force_complete,
        "missing_fields": missing_fields,
    })

@resident_only
def book_delivery(request):
    resident_profile = _get_resident_profile(request.user)
    redirect_response = _redirect_if_profile_incomplete(request, resident_profile)
    if redirect_response:
        return redirect_response
    deliveries = DeliveryItem.objects.filter(resident=request.user).order_by("-created_at")

    def render_page(toast_success=None, toast_error=None, delivery_rows=None, payment_prefill=None):
        payment_prefill = payment_prefill or {}
        raw_amount = payment_prefill.get("payment_amount", f"{WATER_DEFAULT_AMOUNT:.2f}")
        try:
            qr_amount = Decimal(str(raw_amount))
            if qr_amount <= 0:
                qr_amount = WATER_DEFAULT_AMOUNT
        except (InvalidOperation, TypeError):
            qr_amount = WATER_DEFAULT_AMOUNT
        return render(request, "resident/book_delivery.html", {
            "resident_profile": resident_profile,
            "deliveries": delivery_rows if delivery_rows is not None else deliveries,
            "toast_success": toast_success,
            "toast_error": toast_error,
            "water_upi_id": WATER_UPI_ID,
            "water_qr_url": _water_qr_url(qr_amount),
            "payment_prefill": payment_prefill,
        })

    if request.method == "POST":
        delivery_type = request.POST.get("delivery_type")
        expected_date = request.POST.get("expected_date")
        skip_start_date = request.POST.get("skip_start_date")
        skip_days_raw = request.POST.get("skip_days", "").strip()
        skip_milk = request.POST.get("skip_milk") == "on"
        skip_newspaper = request.POST.get("skip_newspaper") == "on"
        vendor = request.POST.get("courier_name")
        instructions = request.POST.get("instructions")
        payment_method = request.POST.get("payment_method", "at_delivery").strip()
        payment_amount_raw = request.POST.get("payment_amount", f"{WATER_DEFAULT_AMOUNT:.2f}").strip()
        payment_reference = request.POST.get("payment_reference", "").strip()

        if delivery_type not in ["skip", "water"]:
            return render_page(toast_error="Please select a delivery type.")

        if delivery_type == "water":
            if payment_method not in {"online", "at_delivery"}:
                return render_page(
                    toast_error="Please select a valid payment option for water booking.",
                    payment_prefill={
                        "payment_method": "at_delivery",
                        "payment_amount": payment_amount_raw,
                        "payment_reference": payment_reference,
                    },
                )

            try:
                payment_amount = Decimal(payment_amount_raw)
            except (InvalidOperation, TypeError):
                payment_amount = Decimal("0")

            if payment_amount <= 0:
                return render_page(
                    toast_error="Enter a valid water booking payment amount.",
                    payment_prefill={
                        "payment_method": payment_method,
                        "payment_amount": payment_amount_raw,
                        "payment_reference": payment_reference,
                    },
                )

            label = "Water Cans Delivery"
            if expected_date:
                label = f"{label} ({expected_date})"

            payment_status = "pending"
            if payment_method == "online" and payment_reference:
                payment_status = "paid"

            water_delivery = DeliveryItem.objects.create(
                resident=request.user,
                carrier=vendor or "Resident Booking",
                label=label,
                status="pending",
                payment_method=payment_method,
                payment_status=payment_status,
                payment_amount=payment_amount,
                payment_reference=payment_reference,
                delivery_otp=_generate_delivery_otp(),
                delivered_at=None,
            )
            method_label = "Online QR" if payment_method == "online" else "Pay at Delivery"
            return render_page(
                toast_success=f"Water cans delivery scheduled successfully with payment mode: {method_label}. Your OTP is {water_delivery.delivery_otp}.",
                delivery_rows=DeliveryItem.objects.filter(resident=request.user).order_by("-created_at"),
            )

        if not skip_milk and not skip_newspaper:
            return render_page(toast_error="Select milk, newspaper, or both for the skip request.")

        try:
            skip_days = int(skip_days_raw)
        except ValueError:
            skip_days = 0

        if skip_days < 1:
            return render_page(toast_error="Enter a valid number of skip days.")

        try:
            start_date = (
                datetime.strptime(skip_start_date, "%Y-%m-%d").date()
                if skip_start_date
                else timezone.localdate()
            )
        except ValueError:
            return render_page(toast_error="Select a valid skip start date.")

        created = _create_skip_deliveries(
            request.user,
            start_date,
            skip_days,
            skip_milk,
            skip_newspaper,
            vendor,
        )
        return render_page(
            toast_success=f"Created {created} skip entr{'y' if created == 1 else 'ies'} starting {start_date:%b %d, %Y}.",
            delivery_rows=DeliveryItem.objects.filter(resident=request.user).order_by("-created_at"),
        )

    return render_page()

@resident_only
def maintenance_request(request):
    resident_profile = _get_resident_profile(request.user)
    redirect_response = _redirect_if_profile_incomplete(request, resident_profile)
    if redirect_response:
        return redirect_response
    requests_qs = MaintenanceRequest.objects.filter(resident=request.user).order_by("-created_at")
    selected_request = None
    selected_id = request.GET.get("request_id")
    if selected_id and selected_id.isdigit():
        selected_request = requests_qs.filter(id=int(selected_id)).first()

    if request.method == "POST":
        category = request.POST.get("category") or "General"
        description = request.POST.get("description")
        priority = request.POST.get("priority")

        if not description:
            return render(request, "resident/maintenance_request.html", {
                "resident_profile": resident_profile,
                "maintenance_requests": requests_qs,
                "selected_request": selected_request,
                "toast_error": "Please describe the issue.",
            })

        title = {
            "plumbing": "Plumbing Issue",
            "electrical": "Electrical Issue",
            "hvac": "HVAC Issue",
            "appliance": "Appliance Issue",
            "other": "Other Issue",
        }.get(category, "Maintenance Request")

        priority_value = "high" if priority == "urgent" else "medium"
        maintenance_req = MaintenanceRequest.objects.create(
            resident=request.user,
            title=title,
            description=description or "",
            status="pending",
            priority=priority_value,
            completion_otp=_generate_maintenance_otp(),
        )
        requests_qs = MaintenanceRequest.objects.filter(resident=request.user).order_by("-created_at")
        return render(request, "resident/maintenance_request.html", {
            "resident_profile": resident_profile,
            "maintenance_requests": requests_qs,
            "selected_request": selected_request,
            "toast_success": f"Maintenance request submitted. Your completion OTP is {maintenance_req.completion_otp}.",
        })

    return render(request, "resident/maintenance_request.html", {
        "resident_profile": resident_profile,
        "maintenance_requests": requests_qs,
        "selected_request": selected_request,
    })


@resident_only
def view_evidence(request, request_id):
    maintenance_req = MaintenanceRequest.objects.filter(id=request_id, resident=request.user).first()
    if not maintenance_req or not maintenance_req.evidence_file:
        raise Http404("Evidence file not found.")
    return FileResponse(maintenance_req.evidence_file.open("rb"), as_attachment=False)

@resident_only
def delivery_status(request):
    resident_profile = _get_resident_profile(request.user)
    redirect_response = _redirect_if_profile_incomplete(request, resident_profile)
    if redirect_response:
        return redirect_response
    deliveries = DeliveryItem.objects.filter(resident=request.user).order_by("-created_at")
    return render(request, "resident/delivery_status.html", {
        "resident_profile": resident_profile,
        "deliveries": deliveries,
    })

@resident_only
def amenities(request):
    resident_profile = _get_resident_profile(request.user)
    redirect_response = _redirect_if_profile_incomplete(request, resident_profile)
    if redirect_response:
        return redirect_response
    amenities_list = Amenity.objects.all().order_by("name")
    amenity_bookings = AmenityBooking.objects.filter(resident=request.user).order_by("-start_time")
    toast_error = None
    toast_success = None

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "cancel":
            booking_id = request.POST.get("booking_id")
            booking = AmenityBooking.objects.filter(id=booking_id, resident=request.user).first()
            if booking:
                booking.status = "cancelled"
                booking.save(update_fields=["status"])
                toast_success = "Booking cancelled."
            else:
                toast_error = "Booking not found."
        else:
            amenity_id = request.POST.get("amenity_id")
            date_str = request.POST.get("booking_date")
            time_str = request.POST.get("booking_time")

            amenity = Amenity.objects.filter(id=amenity_id).first()
            if not amenity:
                toast_error = "Please choose a valid amenity."
            else:
                try:
                    start_time = datetime.fromisoformat(f"{date_str}T{time_str}")
                    start_time = timezone.make_aware(start_time)
                except Exception:
                    start_time = None

                if not start_time:
                    toast_error = "Please select a valid date and time."
                else:
                    open_dt = start_time.replace(
                        hour=amenity.open_time.hour, minute=amenity.open_time.minute, second=0, microsecond=0
                    )
                    close_dt = start_time.replace(
                        hour=amenity.close_time.hour, minute=amenity.close_time.minute, second=0, microsecond=0
                    )
                    if not (open_dt <= start_time < close_dt):
                        toast_error = "Selected time is outside amenity hours."
                    else:
                        end_time = start_time + timedelta(minutes=amenity.slot_minutes)
                        try:
                            AmenityBooking.objects.create(
                                resident=request.user,
                                amenity=amenity,
                                amenity_name=amenity.name,
                                status="booked",
                                start_time=start_time,
                                end_time=end_time,
                            )
                            toast_success = "Booking created."
                        except IntegrityError:
                            toast_error = "This time slot is already booked."

    return render(request, "resident/amenities.html", {
        "resident_profile": resident_profile,
        "amenity_bookings": amenity_bookings,
        "amenities_list": amenities_list,
        "toast_error": toast_error,
        "toast_success": toast_success,
    })

@resident_only
def notices(request):
    resident_profile = _get_resident_profile(request.user)
    redirect_response = _redirect_if_profile_incomplete(request, resident_profile)
    if redirect_response:
        return redirect_response
    now = timezone.now()
    notices = ResidentNotice.objects.filter(publish_from__lte=now).filter(
        Q(publish_until__isnull=True) | Q(publish_until__gte=now)
    ).order_by("-publish_from")
    return render(request, "resident/notices.html", {
        "resident_profile": resident_profile,
        "notices": notices,
    })
