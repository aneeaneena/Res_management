from types import SimpleNamespace
from datetime import datetime

from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone
from accounts.decorators import delivery_only
from accounts.models import Profile
from resident.models import DeliveryItem, ResidentProfile


def _type_filter(delivery_type):
    if delivery_type == "milk":
        return Q(label__icontains="milk") | Q(label__icontains="newspaper")
    if delivery_type == "water":
        return Q(label__icontains="water")
    return Q(pk__in=[])


def _attach_resident_info(deliveries):
    resident_ids = {d.resident_id for d in deliveries}
    profiles = ResidentProfile.objects.filter(user_id__in=resident_ids).select_related("user")
    profile_map = {p.user_id: p for p in profiles}
    for item in deliveries:
        profile = profile_map.get(item.resident_id)
        item.resident_name = item.resident.username
        item.unit = profile.unit if profile else ""
        item.building = profile.building if profile else ""
    return deliveries


def _filter_for_service_date(deliveries_qs, target_date):
    """
    Match deliveries meant for a service date.
    Resident bookings store planned date in label like: "... (YYYY-MM-DD)".
    Keep created_at fallback for records without planned date in label.
    """
    date_str = target_date.strftime("%Y-%m-%d")
    return deliveries_qs.filter(
        Q(label__icontains=f"({date_str})") | Q(created_at__date=target_date)
    )


def _resident_directory():
    resident_profiles = ResidentProfile.objects.select_related("user").order_by("building", "unit", "user__username")
    return {profile.user_id: profile for profile in resident_profiles}


@delivery_only
def security_dashboard(request):
    toast_success = None
    toast_error = None

    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        if action == "verify_delivery_otp":
            delivery_id = request.POST.get("delivery_id", "").strip()
            otp_input = request.POST.get("delivery_otp", "").strip()
            delivery = DeliveryItem.objects.filter(id=delivery_id).filter(_type_filter("water")).first()
            if not delivery:
                toast_error = "Water delivery entry not found."
            elif delivery.status == "delivered":
                toast_error = "This delivery is already marked as delivered."
            elif not otp_input or len(otp_input) != 6 or not otp_input.isdigit():
                toast_error = "Enter a valid 6-digit OTP."
            elif not delivery.delivery_otp:
                toast_error = "OTP is not available for this booking yet."
            elif otp_input != delivery.delivery_otp:
                toast_error = "Incorrect OTP. Please verify with the resident."
            else:
                delivery.status = "delivered"
                delivery.delivered_at = timezone.now()
                delivery.otp_verified_at = timezone.now()
                if delivery.payment_method == "at_delivery":
                    delivery.payment_status = "paid"
                    delivery.save(update_fields=["status", "delivered_at", "otp_verified_at", "payment_status"])
                else:
                    delivery.save(update_fields=["status", "delivered_at", "otp_verified_at"])
                toast_success = f"Delivery #{delivery.id} marked as delivered after OTP verification."

    today = timezone.localdate()
    resident_map = _resident_directory()
    resident_ids = list(resident_map.keys())

    water_deliveries = list(
        _filter_for_service_date(
            DeliveryItem.objects.filter(_type_filter("water")),
            today,
        ).order_by("status", "created_at")
    )
    _attach_resident_info(water_deliveries)

    skipped_ids = set(
        _filter_for_service_date(
            DeliveryItem.objects.filter(_type_filter("milk"), status="skipped"),
            today,
        ).values_list("resident_id", flat=True)
    )

    essentials_deliveries = []
    for resident_id in resident_ids:
        if resident_id in skipped_ids:
            continue
        profile = resident_map[resident_id]
        essentials_deliveries.append(SimpleNamespace(
            resident_name=profile.user.username,
            building=profile.building,
            unit=profile.unit,
            item_label="Milk & Newspaper",
            status="scheduled",
        ))

    skipped_deliveries = list(
        _filter_for_service_date(
            DeliveryItem.objects.filter(_type_filter("milk"), status="skipped"),
            today,
        ).order_by("created_at")
    )
    _attach_resident_info(skipped_deliveries)

    counts = {
        "water": len(water_deliveries),
        "essentials": len(essentials_deliveries),
        "skipped": len(skipped_deliveries),
        "residents": len(resident_ids),
    }
    user_profile = Profile.objects.filter(user=request.user).first()

    return render(request, "delivery/dashboardwater.html", {
        "today": today,
        "water_deliveries": water_deliveries,
        "essentials_deliveries": essentials_deliveries,
        "skipped_deliveries": skipped_deliveries,
        "counts": counts,
        "user_profile": user_profile,
        "toast_success": toast_success,
        "toast_error": toast_error,
    })
