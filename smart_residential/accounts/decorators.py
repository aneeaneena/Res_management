from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @login_required(login_url='login')
        def wrapper_func(request, *args, **kwargs):
            if request.user.profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('login')  # Or a 403 Forbidden page
        return wrapper_func
    return decorator

def resident_only(view_func):
    return role_required(['resident'])(view_func)

def admin_only(view_func):
    return role_required(['admin'])(view_func)

def delivery_only(view_func):
    return role_required(['delivery'])(view_func)

def maintenance_only(view_func):
    return role_required(['maintenance'])(view_func)
