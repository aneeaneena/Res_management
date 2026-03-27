from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.cache import add_never_cache_headers
from .models import Profile
from resident.models import ResidentProfile


def register_view(request):
    allowed_roles = {"resident", "delivery", "maintenance"}

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        role = request.POST.get("role", "").strip()
        unit = request.POST.get("unit", "").strip()
        building = request.POST.get("building", "").strip()
        application_document = request.FILES.get("application_document")

        if not username or not role:
            return render(request, "accounts/register.html", {
                "error": "Username and role are required.",
                "role": role,
            })

        if role not in allowed_roles:
            return render(request, "accounts/register.html", {
                "error": "Invalid role selected.",
                "role": role,
            })

        if User.objects.filter(username=username).exists():
            return render(request, "accounts/register.html", {
                "error": "Username already exists. Please choose a different one.",
                "role": role,
            })

        user = User.objects.create_user(
            username=username,
            email=email,
        )
        user.set_unusable_password()
        user.is_active = False
        user.save(update_fields=["password", "is_active"])

        Profile.objects.create(
            user=user,
            role=role,
            delivery_type=None,
            application_document=application_document,
        )
        if role == "resident":
            ResidentProfile.objects.update_or_create(
                user=user,
                defaults={"unit": unit, "building": building},
            )

        return redirect("login")

    role = request.GET.get('role', '').strip()
    if role not in allowed_roles:
        return redirect('home')

    return render(request, 'accounts/register.html', {'role': role})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = User.objects.filter(username=username).select_related("profile").first()
        if not user:
            return render(request, 'accounts/login.html', {
                'error': 'Invalid username or password',
            })

        try:
            if not user.is_active:
                return render(request, 'accounts/login.html', {
                    'error': 'Your account is pending approval. Please wait for admin approval.',
                })

            if not user.has_usable_password():
                return render(request, 'accounts/login.html', {
                    'error': 'Your account has not been assigned a password by the admin yet.',
                })

            user = authenticate(request, username=username, password=password)
            if user is None:
                return render(request, 'accounts/login.html', {
                    'error': 'Invalid username or password',
                })

            login(request, user)
            role = user.profile.role

            if role == 'resident':
                return redirect('resident_dashboard')

            if role == 'delivery':
                return redirect('delivery_dashboard')

            if role == 'maintenance':
                return redirect('maintenance_dashboard')

            if role == 'admin':
                return redirect('admin_dashboard')

            return render(request, 'accounts/login.html', {
                'error': 'Invalid role configured for this account.',
            })
        except Profile.DoesNotExist:
            return render(request, 'accounts/login.html', {
                'error': 'Profile not found. Please contact an admin to assign your role.',
            })

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    response = redirect('home')
    add_never_cache_headers(response)
    return response


@login_required(login_url="login")
def account_profile(request):
    default_role = "admin" if request.user.is_superuser else "resident"
    user_profile, _ = Profile.objects.get_or_create(user=request.user, defaults={"role": default_role})
    toast_success = None
    toast_error = None

    if request.method == "POST":
        action = request.POST.get("action", "update_profile")
        if action == "upload_profile_picture":
            profile_picture = request.FILES.get("profile_picture")
            if not profile_picture:
                toast_error = "Please choose an image file."
            elif not str(profile_picture.content_type or "").startswith("image/"):
                toast_error = "Only image files are allowed."
            else:
                user_profile.profile_picture = profile_picture
                user_profile.save(update_fields=["profile_picture"])
                toast_success = "Profile picture updated successfully."
        else:
            request.user.username = request.POST.get("username", request.user.username).strip()
            request.user.email = request.POST.get("email", request.user.email).strip()
            request.user.save(update_fields=["username", "email"])

            user_profile.phone = request.POST.get("phone", user_profile.phone).strip()
            user_profile.save(update_fields=["phone"])
            toast_success = "Profile updated successfully."

    return render(request, "accounts/profile.html", {
        "user_profile": user_profile,
        "toast_success": toast_success,
        "toast_error": toast_error,
    })
