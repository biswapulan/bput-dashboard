from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.utils import timezone

from .models import AttendanceLog, CustomUser

INTERN_ROLES = {CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN}


@receiver(user_logged_out)
def record_logout_time(sender, request, user, **kwargs):
    if not user or user.role not in INTERN_ROLES:
        return
    now = timezone.now()
    AttendanceLog.objects.filter(
        user=user,
        login_date=now.date(),
    ).update(logout_time=now)
