from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, Submission, Ticket


class DashboardUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "role", "password1", "password2")


class ContentSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ("semester", "material_type", "subject_code_or_task_title", "submission_link")
        labels = {
            "subject_code_or_task_title": "Subject code",
            "submission_link": "Cloud storage URL",
        }

    def clean_material_type(self):
        material_type = self.cleaned_data["material_type"]
        allowed = {
            Submission.MaterialType.NOTES,
            Submission.MaterialType.PYQ,
            Submission.MaterialType.BOOK,
        }
        if material_type not in allowed:
            raise forms.ValidationError("Content submissions must be Notes, PYQ, or Book material.")
        return material_type

    def clean_submission_link(self):
        link = self.cleaned_data["submission_link"]
        allowed_domains = ("drive.google.com", "docs.google.com", "onedrive.live.com", "dropbox.com")
        if not any(domain in link.lower() for domain in allowed_domains):
            raise forms.ValidationError("Use a shared cloud storage link such as Google Drive.")
        return link


class TechSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ("material_type", "subject_code_or_task_title", "submission_link")
        labels = {
            "subject_code_or_task_title": "Task title or description",
            "submission_link": "GitHub repository or pull request URL",
        }

    def clean_material_type(self):
        material_type = self.cleaned_data["material_type"]
        allowed = {Submission.MaterialType.CODE_FIX, Submission.MaterialType.FEATURE_DEV}
        if material_type not in allowed:
            raise forms.ValidationError("Tech submissions must be Code Fix or Feature Development.")
        return material_type

    def clean_submission_link(self):
        link = self.cleaned_data["submission_link"]
        if "github.com" not in link.lower():
            raise forms.ValidationError("Use a valid GitHub repository or pull request URL.")
        return link


class ReviewSubmissionForm(forms.Form):
    remark = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ("subject", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }
