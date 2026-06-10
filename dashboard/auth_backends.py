from django.contrib.auth.backends import ModelBackend
from .models import CustomUser


class InternIdOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None
        # Try username first
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            # Try intern_id (case-insensitive prefix match)
            try:
                user = CustomUser.objects.get(intern_id__iexact=username)
            except CustomUser.DoesNotExist:
                return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


InternIDOrUsernameBackend = InternIdOrUsernameBackend
