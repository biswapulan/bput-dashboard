from django.utils import timezone

from .models import AttendanceLog


class AttendanceLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_log_attendance(request):
            now = timezone.now()
            AttendanceLog.objects.get_or_create(
                user=request.user,
                login_date=now.date(),
                defaults={"first_login_time": now},
            )
        return self.get_response(request)

    def _should_log_attendance(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return request.path.startswith("/dashboard") or request.path == "/"
