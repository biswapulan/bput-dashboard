from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    ContentSubmissionForm,
    DashboardUserCreationForm,
    ReviewSubmissionForm,
    TechSubmissionForm,
    TicketForm,
)
from .models import AttendanceLog, CustomUser, Submission, Ticket


def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                return HttpResponseForbidden("Access Denied")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


@login_required
def dashboard_home(request):
    role_routes = {
        CustomUser.Role.ADMIN: "admin-dashboard",
        CustomUser.Role.CONTENT_SUPERVISOR: "content-supervisor-dashboard",
        CustomUser.Role.TECH_SUPERVISOR: "tech-supervisor-dashboard",
        CustomUser.Role.CONTENT_INTERN: "content-intern-dashboard",
        CustomUser.Role.TECH_INTERN: "tech-intern-dashboard",
    }
    return redirect(role_routes.get(request.user.role, "login"))


@role_required(CustomUser.Role.ADMIN)
def admin_dashboard(request):
    form = DashboardUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created successfully.")
        return redirect("admin-dashboard")

    today = timezone.localdate()
    attendance = (
        CustomUser.objects.filter(role__in=[CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN])
        .annotate(
            present_days=Count(
                "attendance_logs__login_date",
                filter=Q(
                    attendance_logs__login_date__year=today.year,
                    attendance_logs__login_date__month=today.month,
                ),
                distinct=True,
            )
        )
        .order_by("role", "username")
    )
    context = {
        "form": form,
        "total_submissions": Submission.objects.count(),
        "pending_submissions": Submission.objects.filter(status=Submission.Status.PENDING).count(),
        "open_tickets": Ticket.objects.filter(status=Ticket.Status.OPEN).count(),
        "attendance": attendance,
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@role_required(CustomUser.Role.CONTENT_SUPERVISOR)
def content_supervisor_dashboard(request):
    return supervisor_dashboard(request, Submission.TaskType.CONTENT, Ticket.Department.CONTENT, "dashboard/content_supervisor.html")


@role_required(CustomUser.Role.TECH_SUPERVISOR)
def tech_supervisor_dashboard(request):
    return supervisor_dashboard(request, Submission.TaskType.TECH, Ticket.Department.TECH, "dashboard/tech_supervisor.html")


def supervisor_dashboard(request, task_type, department, template_name):
    submissions = Submission.objects.select_related("intern").filter(task_type=task_type, status=Submission.Status.PENDING)
    tickets = Ticket.objects.select_related("raised_by").filter(department=department, status=Ticket.Status.OPEN)
    return render(request, template_name, {"submissions": submissions, "tickets": tickets})


@role_required(CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR)
def review_submission(request, submission_id, decision):
    submission = get_object_or_404(Submission, pk=submission_id)
    role_task_map = {
        CustomUser.Role.CONTENT_SUPERVISOR: Submission.TaskType.CONTENT,
        CustomUser.Role.TECH_SUPERVISOR: Submission.TaskType.TECH,
    }
    if submission.task_type != role_task_map[request.user.role]:
        return HttpResponseForbidden("Access Denied")
    if decision not in {"approve", "reject"}:
        return HttpResponseForbidden("Access Denied")

    form = ReviewSubmissionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        submission.supervisor_remark = form.cleaned_data["remark"]
        submission.status = Submission.Status.ACCEPTED if decision == "approve" else Submission.Status.REJECTED
        submission.save(update_fields=["supervisor_remark", "status", "updated_at"])
        messages.success(request, "Submission reviewed.")

    return redirect("content-supervisor-dashboard" if submission.task_type == Submission.TaskType.CONTENT else "tech-supervisor-dashboard")


@role_required(CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR)
def resolve_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    allowed_department = Ticket.Department.CONTENT if request.user.role == CustomUser.Role.CONTENT_SUPERVISOR else Ticket.Department.TECH
    if ticket.department != allowed_department:
        return HttpResponseForbidden("Access Denied")
    if request.method == "POST":
        ticket.status = Ticket.Status.RESOLVED
        ticket.save(update_fields=["status"])
        messages.success(request, "Ticket resolved.")
    return redirect("content-supervisor-dashboard" if ticket.department == Ticket.Department.CONTENT else "tech-supervisor-dashboard")


@role_required(CustomUser.Role.CONTENT_INTERN)
def content_intern_dashboard(request):
    submission_form = ContentSubmissionForm(request.POST or None, prefix="submission")
    ticket_form = TicketForm(request.POST or None, prefix="ticket")
    if request.method == "POST" and "submit_content" in request.POST and submission_form.is_valid():
        submission = submission_form.save(commit=False)
        submission.intern = request.user
        submission.task_type = Submission.TaskType.CONTENT
        submission.save()
        messages.success(request, "Content submission sent for review.")
        return redirect("content-intern-dashboard")
    if request.method == "POST" and "raise_ticket" in request.POST and ticket_form.is_valid():
        ticket = ticket_form.save(commit=False)
        ticket.raised_by = request.user
        ticket.department = Ticket.Department.CONTENT
        ticket.save()
        messages.success(request, "Support ticket raised.")
        return redirect("content-intern-dashboard")

    return render(request, "dashboard/content_intern.html", intern_context(request, submission_form, ticket_form))


@role_required(CustomUser.Role.TECH_INTERN)
def tech_intern_dashboard(request):
    submission_form = TechSubmissionForm(request.POST or None, prefix="submission")
    ticket_form = TicketForm(request.POST or None, prefix="ticket")
    if request.method == "POST" and "submit_tech" in request.POST and submission_form.is_valid():
        submission = submission_form.save(commit=False)
        submission.intern = request.user
        submission.task_type = Submission.TaskType.TECH
        submission.semester = None
        submission.save()
        messages.success(request, "Tech submission sent for review.")
        return redirect("tech-intern-dashboard")
    if request.method == "POST" and "raise_ticket" in request.POST and ticket_form.is_valid():
        ticket = ticket_form.save(commit=False)
        ticket.raised_by = request.user
        ticket.department = Ticket.Department.TECH
        ticket.save()
        messages.success(request, "Support ticket raised.")
        return redirect("tech-intern-dashboard")

    return render(request, "dashboard/tech_intern.html", intern_context(request, submission_form, ticket_form))


def intern_context(request, submission_form, ticket_form):
    return {
        "submission_form": submission_form,
        "ticket_form": ticket_form,
        "submissions": request.user.submissions.all(),
        "tickets": request.user.tickets.all(),
    }

# Create your views here.
