from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import datetime
from accounts.decorators import maintenance_only
from accounts.models import Profile
from resident.models import MaintenanceRequest, ResidentProfile


def _classify_task(task):
    combined = f"{task.title or ''} {task.description or ''} {task.location or ''}".lower()
    if "plumb" in combined or "leak" in combined or "pipe" in combined or "tap" in combined:
        return "plumbing"
    if "elect" in combined or "wiring" in combined or "switch" in combined or "power" in combined or "light" in combined:
        return "electrical"
    return "other"


@maintenance_only
def dashboard(request):
    issue_type = request.GET.get("issue_type", "all").strip().lower()
    if issue_type not in {"all", "plumbing", "electrical"}:
        issue_type = "all"

    tasks_qs = MaintenanceRequest.objects.filter(
        assigned_to=request.user,
        assigned_to__profile__role="maintenance",
    ).select_related("resident", "resident__profile").order_by("-created_at")
    all_tasks = list(tasks_qs)

    plumbing_count = 0
    electrical_count = 0
    public_count = 0
    tasks = []
    for task in all_tasks:
        task.issue_type = _classify_task(task)
        task.is_public_request = bool(
            hasattr(task.resident, "profile") and task.resident.profile.role == "admin"
        )
        if task.is_public_request:
            task.otp_state = "not_required"
        elif task.otp_verified_at:
            task.otp_state = "verified"
        else:
            task.otp_state = "pending_verification"
        if task.issue_type == "plumbing":
            plumbing_count += 1
        if task.issue_type == "electrical":
            electrical_count += 1
        if task.is_public_request:
            public_count += 1

        if issue_type == "all" or task.issue_type == issue_type:
            tasks.append(task)

    today = timezone.localdate()
    counts = {
        "due_today": tasks_qs.filter(due_date__date=today).count(),
        "pending": tasks_qs.filter(status="pending").count(),
        "in_progress": tasks_qs.filter(status="in_progress").count(),
        "completed": tasks_qs.filter(status="completed").count(),
        "plumbing": plumbing_count,
        "electrical": electrical_count,
        "public": public_count,
    }
    user_profile = Profile.objects.filter(user=request.user).first()
    return render(request, 'maintenance/dashboard.html', {
        "tasks": tasks,
        "total_tasks": len(tasks),
        "total_assigned_tasks": len(all_tasks),
        "counts": counts,
        "user_profile": user_profile,
        "issue_type": issue_type,
    })

@maintenance_only
def update_task(request, task_id):
    task = get_object_or_404(MaintenanceRequest, id=task_id, assigned_to=request.user)
    toast_success = None
    toast_error = None
    user_profile = Profile.objects.filter(user=request.user).first()
    is_public_request = bool(
        hasattr(task.resident, "profile") and task.resident.profile.role == "admin"
    )

    if request.method == "POST":
        status = request.POST.get("status")
        comments = request.POST.get("comments")
        due_date = request.POST.get("due_date")
        evidence = request.FILES.get("evidence_file")
        completion_otp = request.POST.get("completion_otp", "").strip()
        if status not in ["pending", "in_progress", "completed", "on_hold"]:
            toast_error = "Please select a valid status."
        else:
            task.status = status
            task.technician_comments = comments or task.technician_comments
            if due_date:
                parsed_due = None
                try:
                    parsed_due = datetime.fromisoformat(due_date)
                    if timezone.is_naive(parsed_due):
                        parsed_due = timezone.make_aware(parsed_due)
                except ValueError:
                    parsed_due = None
                if parsed_due:
                    task.due_date = parsed_due
                else:
                    toast_error = "Please select a valid due date."
            if evidence:
                task.evidence_file = evidence
            if (
                not toast_error
                and status == "completed"
                and not is_public_request
                and not task.otp_verified_at
            ):
                if not task.completion_otp:
                    toast_error = "Completion OTP is not available for this request."
                elif not completion_otp or not completion_otp.isdigit() or len(completion_otp) != 6:
                    toast_error = "Enter a valid 6-digit resident OTP to complete this task."
                elif completion_otp != task.completion_otp:
                    toast_error = "Incorrect resident OTP. Please verify with the resident."
                else:
                    task.otp_verified_at = timezone.now()
            if not toast_error:
                task.save()
                toast_success = "Task updated successfully."

    return render(request, 'maintenance/update_task.html', {
        "task": task,
        "toast_success": toast_success,
        "toast_error": toast_error,
        "user_profile": user_profile,
        "is_public_request": is_public_request,
    })
