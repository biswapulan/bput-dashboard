from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm

from .models import Announcement, AssignedTask, CustomUser, Submission, Ticket


class DashboardAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Username or Intern ID")


class DashboardUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "college_name",
            "department",
            "year",
            "role",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (CustomUser.Role.CONTENT_INTERN, "Content Intern"),
            (CustomUser.Role.TECH_INTERN, "Tech Intern"),
        ]

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        department = cleaned_data.get("department")
        if role == CustomUser.Role.CONTENT_INTERN and department != CustomUser.Department.CONTENT:
            self.add_error("department", "Content interns must be in the Content department.")
        if role == CustomUser.Role.TECH_INTERN and department != CustomUser.Department.TECH:
            self.add_error("department", "Tech interns must be in the Tech department.")
        return cleaned_data


class ProfileUpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = ("email",)


class AssignTaskForm(forms.ModelForm):
    intern_id = forms.CharField(
        max_length=40,
        label="Intern ID",
        help_text="Enter the intern's ID to assign the task",
    )

    class Meta:
        model = AssignedTask
        fields = ("title", "description", "task_link")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "description": "Brief description (keep it short to save storage)",
            "task_link": "Link to detailed task file (any URL)",
        }

    def clean_intern_id(self):
        intern_id = self.cleaned_data["intern_id"].strip()
        try:
            user = CustomUser.objects.get(intern_id=intern_id)
        except CustomUser.DoesNotExist:
            raise forms.ValidationError("No intern found with this ID.")
        return intern_id


class SubmitTaskForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ("submission_link", "note")
        labels = {
            "submission_link": "Submission Link",
            "note": "Note to supervisor (optional)",
        }
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class ReviewTaskForm(forms.Form):
    remark = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label="Remark (required on rejection)",
    )


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ("subject", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ("title", "body")
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),
        }
