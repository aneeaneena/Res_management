from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.decorators import admin_only
from accounts.models import Profile
from resident.models import (
    Amenity,
    AmenityBooking,
    DeliveryItem,
    MaintenanceRequest,
    ResidentNotice,
    ResidentProfile,
)


ALLOWED_MAINTENANCE_STATUSES = {"pending", "in_progress", "completed", "on_hold"}
ALLOWED_DELIVERY_STATUSES = {"pending", "ready", "picked_up", "delivered", "skipped"}
ALLOWED_BOOKING_STATUSES = {"booked", "completed", "cancelled"}
APPROVAL_ROLES = {"resident", "delivery", "maintenance"}

@admin_only
def dashboard(request):
    user_profile = Profile.objects.filter(user=request.user).first()
    return render(request, 'adminpanel/dashboard.html', {
        "user_profile": user_profile,
    })

@admin_only
def approve_residents(request):
    toast_success = None
    toast_error = None
    selected_role = request.GET.get("role", "resident").strip()
    if selected_role not in APPROVAL_ROLES:
        selected_role = "resident"

    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")
        selected_role = request.POST.get("role", selected_role).strip()
        if selected_role not in APPROVAL_ROLES:
            selected_role = "resident"
        new_password = request.POST.get("new_password", "").strip()
        user = User.objects.filter(id=user_id, profile__role=selected_role).first()
        if not user:
            toast_error = "Applicant not found."
        else:
            if action == "approve":
                if not new_password:
                    toast_error = "A password is required for approval."
                else:
                    user.is_active = True
                    user.set_password(new_password)
                    user.save(update_fields=["is_active", "password"])
                    toast_success = "Applicant approved."
            elif action == "reject":
                user.is_active = False
                user.save(update_fields=["is_active"])
                toast_success = "Applicant rejected."
            else:
                toast_error = "Invalid action."

    query = request.GET.get("q", "").strip()
    date_filter = request.GET.get("date_filter", "all")
    users = User.objects.filter(profile__role=selected_role).select_related("profile")
    if query:
        search_filter = Q(username__icontains=query) | Q(email__icontains=query)
        if selected_role == "resident":
            search_filter |= Q(resident_profile__unit__icontains=query) | Q(resident_profile__building__icontains=query)
        if selected_role == "delivery":
            search_filter |= Q(profile__delivery_type__icontains=query)
        users = users.filter(search_filter)
    if date_filter in {"today", "week", "month"}:
        now = timezone.now()
        if date_filter == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == "week":
            start = now - timedelta(days=7)
        else:
            start = now - timedelta(days=30)
        users = users.filter(date_joined__gte=start)
    users = users.order_by("username")
    resident_profiles = ResidentProfile.objects.filter(user__in=users)
    profile_map = {rp.user_id: rp for rp in resident_profiles}

    residents = []
    for user in users:
        rp = profile_map.get(user.id)
        profile_document_url = user.profile.application_document.url if user.profile.application_document else ""
        lease_url = rp.lease_file.url if rp and rp.lease_file else ""
        if user.profile.role == "resident":
            document_url = lease_url or profile_document_url
        else:
            document_url = profile_document_url

        residents.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "unit": rp.unit if rp else "",
            "building": rp.building if rp else "",
            "role": user.profile.role,
            "delivery_type": user.profile.delivery_type or "",
            "is_active": user.is_active,
            "lease_url": lease_url,
            "document_url": document_url,
            "date_submitted": user.date_joined,
        })

    pending_count = sum(1 for resident in residents if not resident["is_active"])
    role_pending_counts = {
        "resident": User.objects.filter(profile__role="resident", is_active=False).count(),
        "delivery": User.objects.filter(profile__role="delivery", is_active=False).count(),
        "maintenance": User.objects.filter(profile__role="maintenance", is_active=False).count(),
    }
    role_labels = {
        "resident": "Resident",
        "delivery": "Delivery Staff",
        "maintenance": "Maintenance Staff",
    }

    return render(request, 'adminpanel/approve_res.html', {
        "residents": residents,
        "pending_count": pending_count,
        "selected_role": selected_role,
        "role_pending_counts": role_pending_counts,
        "role_label": role_labels[selected_role],
        "toast_success": toast_success,
        "toast_error": toast_error,
        "query": query,
        "date_filter": date_filter,
    })

@admin_only
def manage_notices(request):
    toast_success = None
    toast_error = None

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            title = request.POST.get("title", "").strip()
            body = request.POST.get("body", "").strip()
            priority = request.POST.get("priority", "normal")
            publish_from_raw = request.POST.get("publish_from")
            publish_until_raw = request.POST.get("publish_until")
            if not title or not body:
                toast_error = "Title and message are required."
            else:
                publish_from = timezone.now()
                publish_until = None
                if publish_from_raw:
                    try:
                        publish_from = datetime.fromisoformat(publish_from_raw)
                        publish_from = timezone.make_aware(publish_from)
                    except ValueError:
                        toast_error = "Invalid publish start date."
                if publish_until_raw:
                    try:
                        publish_until = datetime.fromisoformat(publish_until_raw)
                        publish_until = timezone.make_aware(publish_until)
                    except ValueError:
                        toast_error = "Invalid publish end date."
                if not toast_error and publish_until and publish_until < publish_from:
                    toast_error = "Publish end date must be after the start date."
                if not toast_error:
                    ResidentNotice.objects.create(
                        title=title,
                        body=body,
                        priority=priority,
                        publish_from=publish_from,
                        publish_until=publish_until,
                    )
                    toast_success = "Notice created."
        elif action == "delete":
            notice_id = request.POST.get("notice_id")
            if ResidentNotice.objects.filter(id=notice_id).exists():
                ResidentNotice.objects.filter(id=notice_id).delete()
                toast_success = "Notice deleted."
            else:
                toast_error = "Notice not found."
        else:
            toast_error = "Invalid action."

    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "all")
    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()

    notices = ResidentNotice.objects.all()
    if query:
        notices = notices.filter(Q(title__icontains=query) | Q(body__icontains=query))
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            start_dt = timezone.make_aware(start_dt)
            notices = notices.filter(publish_from__gte=start_dt)
        except ValueError:
            toast_error = "Invalid start date filter."
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            end_dt = timezone.make_aware(end_dt)
            notices = notices.filter(publish_from__lte=end_dt)
        except ValueError:
            toast_error = "Invalid end date filter."

    now = timezone.now()
    if status_filter == "active":
        notices = notices.filter(publish_from__lte=now).filter(
            Q(publish_until__isnull=True) | Q(publish_until__gte=now)
        )
    elif status_filter == "expired":
        notices = notices.filter(publish_until__isnull=False, publish_until__lt=now)
    elif status_filter == "draft":
        notices = notices.filter(publish_from__gt=now)

    notices = notices.order_by("-publish_from")
    for notice in notices:
        if notice.publish_from and notice.publish_from > now:
            notice.status_label = "Draft"
        elif notice.publish_until and notice.publish_until < now:
            notice.status_label = "Expired"
        else:
            notice.status_label = "Active"

    return render(request, 'adminpanel/manage_notices.html', {
        "notices": notices,
        "toast_success": toast_success,
        "toast_error": toast_error,
        "query": query,
        "status_filter": status_filter,
        "start_date": start_date,
        "end_date": end_date,
    })

@admin_only
def manage_deliveries(request):
    toast_success = None
    toast_error = None

    if request.method == "POST":
        action = request.POST.get("action")
        delivery_id = request.POST.get("delivery_id")
        if action == "update_status":
            status = request.POST.get("status")
            if status not in ALLOWED_DELIVERY_STATUSES:
                toast_error = "Invalid status."
            else:
                delivery = DeliveryItem.objects.filter(id=delivery_id).first()
                if not delivery:
                    toast_error = "Delivery not found."
                else:
                    delivery.status = status
                    delivery.save(update_fields=["status"])
                    toast_success = "Delivery status updated."
        elif action == "create":
            resident_id = request.POST.get("resident_id")
            carrier = request.POST.get("carrier", "").strip()
            label = request.POST.get("label", "").strip()
            status = request.POST.get("status", "pending")
            if not resident_id or not carrier or not label:
                toast_error = "Resident, carrier, and label are required."
            elif status not in ALLOWED_DELIVERY_STATUSES:
                toast_error = "Invalid status."
            else:
                resident = User.objects.filter(id=resident_id).first()
                if not resident:
                    toast_error = "Resident not found."
                else:
                    DeliveryItem.objects.create(
                        resident=resident,
                        carrier=carrier,
                        label=label,
                        status=status,
                    )
                    toast_success = "Delivery logged."
        else:
            toast_error = "Invalid action."

    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    range_filter = request.GET.get("range", "").strip()

    deliveries = DeliveryItem.objects.select_related("resident")
    if query:
        deliveries = deliveries.filter(
            Q(resident__username__icontains=query)
            | Q(carrier__icontains=query)
            | Q(label__icontains=query)
            | Q(id__icontains=query)
        )
    if status_filter in ALLOWED_DELIVERY_STATUSES:
        deliveries = deliveries.filter(status=status_filter)
    if range_filter in {"7", "30", "today"}:
        now = timezone.now()
        if range_filter == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now - timedelta(days=int(range_filter))
        deliveries = deliveries.filter(created_at__gte=start)

    deliveries = deliveries.order_by("-created_at")
    resident_profiles = ResidentProfile.objects.filter(user__in=deliveries.values_list("resident_id", flat=True))
    profile_map = {rp.user_id: rp for rp in resident_profiles}
    delivery_rows = []
    for item in deliveries:
        profile = profile_map.get(item.resident_id)
        delivery_rows.append({
            "id": item.id,
            "resident": item.resident,
            "unit": profile.unit if profile else "",
            "building": profile.building if profile else "",
            "carrier": item.carrier,
            "label": item.label,
            "status": item.status,
            "created_at": item.created_at,
        })

    residents = User.objects.filter(profile__role="resident").order_by("username")
    pending_count = DeliveryItem.objects.filter(status="pending").count()
    collected_count = DeliveryItem.objects.filter(status__in=["picked_up", "delivered"]).count()
    returned_count = DeliveryItem.objects.filter(status="skipped").count()
    show_new_form = request.GET.get("new") == "1"
    return render(request, 'adminpanel/manage_deliveries.html', {
        "deliveries": delivery_rows,
        "residents": residents,
        "toast_success": toast_success,
        "toast_error": toast_error,
        "query": query,
        "status_filter": status_filter,
        "range_filter": range_filter,
        "pending_count": pending_count,
        "collected_count": collected_count,
        "returned_count": returned_count,
        "show_new_form": show_new_form,
    })

@admin_only
def assign_maintenance(request):
    toast_success = None
    toast_error = None

    if request.method == "POST":
        action = request.POST.get("action")
        request_id = request.POST.get("request_id")
        if action == "update_status":
            status = request.POST.get("status")
            if status not in ALLOWED_MAINTENANCE_STATUSES:
                toast_error = "Invalid status."
            else:
                req = MaintenanceRequest.objects.filter(id=request_id).first()
                if not req:
                    toast_error = "Maintenance request not found."
                elif status in {"in_progress", "completed", "on_hold"} and not req.assigned_to:
                    toast_error = "Assign a maintenance staff before changing this status."
                else:
                    req.status = status
                    if status == "in_progress" and not req.due_date:
                        req.due_date = timezone.now()
                    req.save(update_fields=["status", "due_date"])
                    toast_success = "Maintenance status updated."
        elif action == "assign_worker":
            worker_id = request.POST.get("worker_id")
            req = MaintenanceRequest.objects.filter(id=request_id).first()
            if not req:
                toast_error = "Maintenance request not found."
            elif not worker_id:
                toast_error = "Please select a worker."
            else:
                worker = User.objects.filter(id=worker_id, profile__role="maintenance").first()
                if not worker:
                    toast_error = "Worker not found."
                else:
                    req.assigned_to = worker
                    if req.status == "pending":
                        req.status = "in_progress"
                    req.save(update_fields=["assigned_to", "status"])
                    toast_success = "Worker assigned."
        elif action == "create_request":
            title = request.POST.get("title", "").strip()
            description = request.POST.get("description", "").strip()
            location = request.POST.get("location", "").strip()
            priority = request.POST.get("priority", "medium")
            if not title:
                toast_error = "Title is required."
            elif priority not in {"low", "medium", "high"}:
                toast_error = "Invalid priority."
            else:
                MaintenanceRequest.objects.create(
                    resident=request.user,
                    title=title,
                    description=description,
                    location=location,
                    priority=priority,
                    status="pending",
                )
                toast_success = "Public maintenance request created."
        else:
            toast_error = "Invalid action."

    requests = MaintenanceRequest.objects.select_related("resident", "resident__profile").order_by("-created_at")
    resident_profiles = ResidentProfile.objects.filter(user__in=requests.values_list("resident_id", flat=True))
    profile_map = {rp.user_id: rp for rp in resident_profiles}
    maintenance_rows = []
    for req in requests:
        profile = profile_map.get(req.resident_id)
        is_public_request = bool(
            hasattr(req.resident, "profile")
            and req.resident.profile.role == "admin"
        )
        maintenance_rows.append({
            "id": req.id,
            "title": req.title,
            "description": req.description,
            "resident": req.resident,
            "requester_label": "Public Request (Admin)" if is_public_request else req.resident.username,
            "unit": "Public Area" if is_public_request else (profile.unit if profile else ""),
            "building": profile.building if profile else "",
            "status": req.status,
            "priority": getattr(req, "priority", "medium"),
            "assigned_to": req.assigned_to,
            "created_at": req.created_at,
        })

    return render(request, 'adminpanel/assign_maintenance.html', {
        "requests": maintenance_rows,
        "toast_success": toast_success,
        "toast_error": toast_error,
        "maintenance_staff": User.objects.filter(profile__role="maintenance").order_by("username"),
    })

@admin_only
def manage_amenities(request):
    toast_success = None
    toast_error = None

    if request.method == "POST":
        action = request.POST.get("action")
        booking_id = request.POST.get("booking_id")
        if action == "update_booking":
            status = request.POST.get("status")
            if status not in ALLOWED_BOOKING_STATUSES:
                toast_error = "Invalid booking status."
            else:
                booking = AmenityBooking.objects.filter(id=booking_id).first()
                if not booking:
                    toast_error = "Booking not found."
                else:
                    booking.status = status
                    booking.save(update_fields=["status"])
                    toast_success = "Booking updated."
        elif action == "create_amenity":
            name = request.POST.get("name", "").strip()
            category = request.POST.get("category", "social")
            open_time = request.POST.get("open_time")
            close_time = request.POST.get("close_time")
            slot_minutes = request.POST.get("slot_minutes") or 60
            if not name or not open_time or not close_time:
                toast_error = "Amenity name and hours are required."
            else:
                Amenity.objects.create(
                    name=name,
                    category=category,
                    open_time=open_time,
                    close_time=close_time,
                    slot_minutes=slot_minutes,
                )
                toast_success = "Amenity created."
        else:
            toast_error = "Invalid action."

    query = request.GET.get("q", "").strip()
    amenity_filter = request.GET.get("amenity_id", "").strip()
    status_filter = request.GET.get("status", "").strip()

    bookings = AmenityBooking.objects.select_related("resident", "amenity")
    if query:
        bookings = bookings.filter(
            Q(resident__username__icontains=query)
            | Q(amenity__name__icontains=query)
            | Q(amenity_name__icontains=query)
        )
    if amenity_filter:
        bookings = bookings.filter(amenity_id=amenity_filter)
    if status_filter in ALLOWED_BOOKING_STATUSES:
        bookings = bookings.filter(status=status_filter)

    bookings = bookings.order_by("-created_at")
    resident_profiles = ResidentProfile.objects.filter(user__in=bookings.values_list("resident_id", flat=True))
    profile_map = {rp.user_id: rp for rp in resident_profiles}
    booking_rows = []
    for booking in bookings:
        profile = profile_map.get(booking.resident_id)
        booking_rows.append({
            "id": booking.id,
            "resident": booking.resident,
            "unit": profile.unit if profile else "",
            "amenity_name": booking.amenity.name if booking.amenity else booking.amenity_name,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "status": booking.status,
        })

    amenities = Amenity.objects.order_by("name")

    return render(request, 'adminpanel/manage_amenities.html', {
        "bookings": booking_rows,
        "amenities": amenities,
        "toast_success": toast_success,
        "toast_error": toast_error,
        "query": query,
        "amenity_filter": amenity_filter,
        "status_filter": status_filter,
    })
