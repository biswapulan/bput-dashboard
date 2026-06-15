from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AnnouncementForm,
    AssignTaskForm,
    DashboardUserCreationForm,
    ProfileUpdateForm,
    ReviewTaskForm,
    SubmitTaskForm,
    TicketForm,
)
from .models import (
    Announcement,
    AnnouncementRead,
    AssignedTask,
    AttendanceLog,
    CustomUser,
    InternAccountRead,
    Submission,
    SubmissionRead,
    TaskRead,
    Ticket,
    TicketRead,
)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                return HttpResponseForbidden("Access Denied")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_unread_counts(user):
    """Returns dict of unread badge counts for sidebar red dots."""
    counts = {}
    role = user.role

    if role in {CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN}:
        # Unread tasks: assigned to this intern, not yet read
        read_task_ids = TaskRead.objects.filter(user=user).values_list("task_id", flat=True)
        counts["unread_tasks"] = AssignedTask.objects.filter(
            assigned_to=user
        ).exclude(id__in=read_task_ids).count()

        # Unread announcements
        read_ann_ids = AnnouncementRead.objects.filter(user=user).values_list("announcement_id", flat=True)
        counts["unread_announcements"] = Announcement.objects.exclude(id__in=read_ann_ids).count()

    if role in {CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR}:
        dept = "CONTENT" if role == CustomUser.Role.CONTENT_SUPERVISOR else "TECH"
        # Unread submissions: submitted against tasks assigned by this supervisor
        read_sub_ids = SubmissionRead.objects.filter(user=user).values_list("submission_id", flat=True)
        counts["unread_submissions"] = Submission.objects.filter(
            task__assigned_by=user,
            status=Submission.Status.PENDING,
        ).exclude(id__in=read_sub_ids).count()

        read_ticket_ids = TicketRead.objects.filter(user=user).values_list("ticket_id", flat=True)
        counts["unread_tickets"] = Ticket.objects.filter(
            department=dept, status=Ticket.Status.OPEN
        ).exclude(id__in=read_ticket_ids).count()

        # Announcements for supervisors
        read_ann_ids = AnnouncementRead.objects.filter(user=user).values_list("announcement_id", flat=True)
        counts["unread_announcements"] = Announcement.objects.exclude(id__in=read_ann_ids).count()

    if role == CustomUser.Role.ADMIN:
        read_ann_ids = AnnouncementRead.objects.filter(user=user).values_list("announcement_id", flat=True)
        counts["unread_announcements"] = Announcement.objects.exclude(id__in=read_ann_ids).count()
        read_intern_ids = InternAccountRead.objects.filter(user=user).values_list("intern_id", flat=True)
        counts["unread_interns"] = CustomUser.objects.filter(
            role__in=[CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN]
        ).exclude(id__in=read_intern_ids).count()

    return counts


# ─── Routing ───────────────────────────────────────────────────────────────────

@login_required
def dashboard_home(request):
    role_routes = {
        CustomUser.Role.ADMIN: "admin-dashboard",
        CustomUser.Role.CONTENT_SUPERVISOR: "tasks",
        CustomUser.Role.TECH_SUPERVISOR: "tasks",
        CustomUser.Role.CONTENT_INTERN: "tasks",
        CustomUser.Role.TECH_INTERN: "tasks",
    }
    return redirect(role_routes.get(request.user.role, "login"))


@login_required
def tasks(request):
    if request.user.role in {CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR}:
        return supervisor_dashboard(request)
    if request.user.role in {CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN}:
        return intern_dashboard(request)
    return redirect("admin-dashboard")


@login_required
def submissions(request):
    return tasks(request)


@login_required
def tickets(request):
    if request.user.role in {CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN}:
        return intern_dashboard(request)
    if request.user.role in {CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR}:
        return supervisor_dashboard(request)
    return redirect("admin-dashboard")


# ─── Admin ─────────────────────────────────────────────────────────────────────

@role_required(CustomUser.Role.ADMIN)
def admin_dashboard(request):
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
    counts = get_unread_counts(request.user)
    context = {
        "total_tasks": AssignedTask.objects.count(),
        "pending_tasks": AssignedTask.objects.filter(status=AssignedTask.Status.PENDING).count(),
        "open_tickets": Ticket.objects.filter(status=Ticket.Status.OPEN).count(),
        "total_interns": CustomUser.objects.filter(
            role__in=[CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN]
        ).count(),
        "attendance": attendance,
        "users": CustomUser.objects.all().order_by("role", "username"),
        **counts,
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@role_required(CustomUser.Role.ADMIN)
def create_intern(request):
    form = DashboardUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Intern account created successfully.")
        return redirect("create-intern")
    counts = get_unread_counts(request.user)
    return render(request, "dashboard/create_intern.html", {"form": form, **counts})


@role_required(CustomUser.Role.ADMIN)
def user_management(request):
    users = CustomUser.objects.all().order_by("role", "username")
    interns = users.filter(role__in=[CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN])
    existing_read_ids = InternAccountRead.objects.filter(
        user=request.user,
    ).values_list("intern_id", flat=True)
    new_reads = [
        InternAccountRead(user=request.user, intern=intern)
        for intern in interns
        if intern.id not in existing_read_ids
    ]
    if new_reads:
        InternAccountRead.objects.bulk_create(new_reads, ignore_conflicts=True)
    counts = get_unread_counts(request.user)
    counts["unread_interns"] = 0
    return render(request, "dashboard/user_management.html", {"users": users, **counts})


@role_required(CustomUser.Role.ADMIN)
def delete_user(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)
    if target_user.pk == request.user.pk:
        messages.error(request, "You cannot delete your own account.")
        return redirect("user-management")
    if request.method == "POST":
        label = target_user.username
        target_user.delete()
        messages.success(request, f"User {label} deleted.")
    return redirect("user-management")


@role_required(CustomUser.Role.ADMIN)
def admin_attendance(request):
    today = timezone.localdate()
    filter_date = request.GET.get("date", "")
    filter_dept = request.GET.get("dept", "")
    filter_intern = request.GET.get("intern", "")

    logs = AttendanceLog.objects.select_related("user").order_by("-login_date", "user__username")

    if filter_date:
        try:
            from datetime import date as date_type
            parsed = date_type.fromisoformat(filter_date)
            logs = logs.filter(login_date=parsed)
        except ValueError:
            pass
    if filter_dept:
        logs = logs.filter(user__department=filter_dept)
    if filter_intern:
        logs = logs.filter(
            Q(user__username__icontains=filter_intern) |
            Q(user__first_name__icontains=filter_intern) |
            Q(user__last_name__icontains=filter_intern) |
            Q(user__intern_id__icontains=filter_intern)
        )

    # Summary stats
    total_interns = CustomUser.objects.filter(
        role__in=[CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN]
    ).count()
    present_today = AttendanceLog.objects.filter(login_date=today).count()
    present_this_month = AttendanceLog.objects.filter(
        login_date__year=today.year, login_date__month=today.month
    ).values("user").distinct().count()

    counts = get_unread_counts(request.user)
    return render(request, "dashboard/attendance.html", {
        "logs": logs,
        "filter_date": filter_date,
        "filter_dept": filter_dept,
        "filter_intern": filter_intern,
        "total_interns": total_interns,
        "present_today": present_today,
        "present_this_month": present_this_month,
        "today": today,
        **counts,
    })


@role_required(CustomUser.Role.ADMIN)
def admin_archive(request):
    tasks = AssignedTask.objects.select_related("assigned_to", "assigned_by").filter(
        status__in=[AssignedTask.Status.ACCEPTED]
    )
    tickets = Ticket.objects.select_related("raised_by").filter(status=Ticket.Status.RESOLVED)
    counts = get_unread_counts(request.user)
    return render(request, "dashboard/admin_archive.html", {"tasks": tasks, "tickets": tickets, **counts})


# ─── Announcements ─────────────────────────────────────────────────────────────

@login_required
def announcements(request):
    if request.method == "POST" and request.user.role == CustomUser.Role.ADMIN:
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.created_by = request.user
            ann.save()
            messages.success(request, "Announcement posted.")
            return redirect("announcements")
    else:
        form = AnnouncementForm()

    all_ann = Announcement.objects.all()

    # Mark all as read for this user
    existing_read_ids = AnnouncementRead.objects.filter(
        user=request.user
    ).values_list("announcement_id", flat=True)
    new_reads = [
        AnnouncementRead(user=request.user, announcement=a)
        for a in all_ann if a.id not in existing_read_ids
    ]
    if new_reads:
        AnnouncementRead.objects.bulk_create(new_reads, ignore_conflicts=True)

    counts = get_unread_counts(request.user)
    counts["unread_announcements"] = 0  # just marked them all read
    return render(request, "dashboard/announcements.html", {
        "announcements": all_ann,
        "form": form,
        "can_post": request.user.role == CustomUser.Role.ADMIN,
        **counts,
    })


@role_required(CustomUser.Role.ADMIN)
def delete_announcement(request, ann_id):
    ann = get_object_or_404(Announcement, ann_id=ann_id)
    if request.method == "POST":
        ann.delete()
        messages.success(request, "Announcement deleted.")
    return redirect("announcements")


# ─── Supervisor ────────────────────────────────────────────────────────────────

@role_required(CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR)
def supervisor_dashboard(request):
    user = request.user
    dept = "CONTENT" if user.role == CustomUser.Role.CONTENT_SUPERVISOR else "TECH"
    intern_role = CustomUser.Role.CONTENT_INTERN if dept == "CONTENT" else CustomUser.Role.TECH_INTERN

    # Tasks assigned by this supervisor
    tasks = AssignedTask.objects.select_related("assigned_to", "submission").filter(
        assigned_by=user,
        status__in=[AssignedTask.Status.PENDING, AssignedTask.Status.SUBMITTED],
    )

    # Mark submissions as read
    sub_ids = [t.submission.id for t in tasks if hasattr(t, "submission") and t.status == AssignedTask.Status.SUBMITTED]
    if sub_ids:
        existing = SubmissionRead.objects.filter(user=user, submission_id__in=sub_ids).values_list("submission_id", flat=True)
        new_reads = [SubmissionRead(user=user, submission_id=sid) for sid in sub_ids if sid not in existing]
        if new_reads:
            SubmissionRead.objects.bulk_create(new_reads, ignore_conflicts=True)

    tickets = Ticket.objects.select_related("raised_by").filter(
        department=dept, status=Ticket.Status.OPEN
    )
    ticket_ids = list(tickets.values_list("id", flat=True))
    if ticket_ids:
        existing_tickets = TicketRead.objects.filter(
            user=user,
            ticket_id__in=ticket_ids,
        ).values_list("ticket_id", flat=True)
        new_ticket_reads = [
            TicketRead(user=user, ticket_id=ticket_id)
            for ticket_id in ticket_ids
            if ticket_id not in existing_tickets
        ]
        if new_ticket_reads:
            TicketRead.objects.bulk_create(new_ticket_reads, ignore_conflicts=True)

    # All interns in this department
    today = timezone.localdate()
    interns = (
        CustomUser.objects.filter(role=intern_role)
        .annotate(
            task_count=Count("assigned_tasks", distinct=True),
            pending_count=Count(
                "assigned_tasks",
                filter=Q(assigned_tasks__status=AssignedTask.Status.PENDING),
                distinct=True,
            ),
            present_this_month=Count(
                "attendance_logs__login_date",
                filter=Q(
                    attendance_logs__login_date__year=today.year,
                    attendance_logs__login_date__month=today.month,
                ),
                distinct=True,
            ),
        )
        .order_by("first_name", "username")
    )

    counts = get_unread_counts(request.user)
    counts["unread_submissions"] = 0
    counts["unread_tickets"] = 0
    return render(request, "dashboard/supervisor_dashboard.html", {
        "tasks": tasks,
        "tickets": tickets,
        "interns": interns,
        "dept": dept,
        **counts,
    })


@role_required(CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR)
def assign_task(request):
    user = request.user
    dept_role = "CONTENT" if user.role == CustomUser.Role.CONTENT_SUPERVISOR else "TECH"
    intern_role = CustomUser.Role.CONTENT_INTERN if dept_role == "CONTENT" else CustomUser.Role.TECH_INTERN

    intern_preview = None
    error_msg = None

    form = AssignTaskForm(request.POST or None)

    if request.method == "POST":
        if "lookup" in request.POST:
            intern_id = request.POST.get("intern_id", "").strip()
            try:
                intern = CustomUser.objects.get(intern_id=intern_id, role=intern_role)
                intern_preview = intern
            except CustomUser.DoesNotExist:
                error_msg = f"No {dept_role.capitalize()} intern found with ID '{intern_id}'."
        elif form.is_valid():
            intern_id = form.cleaned_data["intern_id"].strip()
            try:
                intern = CustomUser.objects.get(intern_id=intern_id, role=intern_role)
            except CustomUser.DoesNotExist:
                form.add_error("intern_id", f"No {dept_role.capitalize()} intern with this ID.")
                counts = get_unread_counts(request.user)
                return render(request, "dashboard/assign_task.html", {"form": form, "intern_preview": None, "error_msg": None, **counts})

            task = form.save(commit=False)
            task.assigned_to = intern
            task.assigned_by = user
            task.save()
            messages.success(request, f"Task {task.task_id} assigned to {intern.get_full_name() or intern.username}.")
            return redirect("tasks")

    counts = get_unread_counts(request.user)
    return render(request, "dashboard/assign_task.html", {
        "form": form,
        "intern_preview": intern_preview,
        "error_msg": error_msg,
        **counts,
    })


@role_required(CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR)
def review_task(request, task_id, decision):
    task = get_object_or_404(AssignedTask, task_id=task_id, assigned_by=request.user)
    if task.status != AssignedTask.Status.SUBMITTED:
        messages.error(request, "Task is not in Submitted state.")
        return redirect("tasks")
    if decision not in {"approve", "reject"}:
        return HttpResponseForbidden()

    if request.method == "POST":
        remark = request.POST.get("remark", "").strip()
        submission = getattr(task, "submission", None)
        if decision == "approve":
            task.status = AssignedTask.Status.ACCEPTED
            if submission:
                submission.status = Submission.Status.ACCEPTED
                submission.supervisor_remark = remark
                submission.save()
            task.rejection_remark = ""
            messages.success(request, f"Task {task.task_id} accepted.")
        else:
            if not remark:
                messages.error(request, "A rejection remark is required.")
                return redirect("tasks")
            task.status = AssignedTask.Status.PENDING  # back to pending for resubmission
            task.rejection_remark = remark
            if submission:
                submission.status = Submission.Status.REJECTED
                submission.supervisor_remark = remark
                submission.save()
                submission.delete()  # Remove submission so intern can resubmit
            messages.warning(request, f"Task {task.task_id} rejected. Intern must resubmit.")
        task.save()
    return redirect("tasks")


@role_required(CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR)
def resolve_ticket(request, token_id):
    allowed_dept = Ticket.Department.CONTENT if request.user.role == CustomUser.Role.CONTENT_SUPERVISOR else Ticket.Department.TECH
    ticket = get_object_or_404(Ticket, token_id=token_id, department=allowed_dept)
    if request.method == "POST":
        ticket.status = Ticket.Status.RESOLVED
        ticket.supervisor_reply = request.POST.get("supervisor_reply", "").strip() or None
        ticket.save()
        messages.success(request, "Ticket resolved.")
    return redirect("tasks")


@role_required(CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR)
def supervisor_archive(request):
    user = request.user
    tasks = AssignedTask.objects.select_related("assigned_to").filter(
        assigned_by=user,
        status__in=[AssignedTask.Status.ACCEPTED, AssignedTask.Status.REJECTED],
    )
    dept = "CONTENT" if user.role == CustomUser.Role.CONTENT_SUPERVISOR else "TECH"
    tickets = Ticket.objects.select_related("raised_by").filter(
        department=dept, status=Ticket.Status.RESOLVED
    )
    counts = get_unread_counts(request.user)
    return render(request, "dashboard/supervisor_archive.html", {
        "tasks": tasks,
        "tickets": tickets,
        **counts,
    })


# ─── Intern ────────────────────────────────────────────────────────────────────

@role_required(CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN)
def intern_dashboard(request):
    tasks = AssignedTask.objects.filter(assigned_to=request.user).select_related("assigned_by")

    # Mark tasks as read (clears red dot)
    existing_read_ids = TaskRead.objects.filter(user=request.user).values_list("task_id", flat=True)
    new_reads = [TaskRead(user=request.user, task=t) for t in tasks if t.id not in existing_read_ids]
    if new_reads:
        TaskRead.objects.bulk_create(new_reads, ignore_conflicts=True)

    tickets = Ticket.objects.filter(raised_by=request.user)
    counts = get_unread_counts(request.user)
    counts["unread_tasks"] = 0

    return render(request, "dashboard/intern_dashboard.html", {
        "tasks": tasks,
        "tickets": tickets,
        **counts,
    })


@role_required(CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN)
def intern_attendance(request):
    logs = AttendanceLog.objects.filter(user=request.user).order_by("-login_date")
    counts = get_unread_counts(request.user)
    return render(request, "dashboard/intern_attendance.html", {
        "logs": logs,
        **counts,
    })


@role_required(CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN)
def submit_task(request, task_id):
    task = get_object_or_404(AssignedTask, task_id=task_id, assigned_to=request.user)

    if task.status not in {AssignedTask.Status.PENDING, AssignedTask.Status.REJECTED}:
        messages.error(request, "This task cannot be submitted right now.")
        return redirect("tasks")

    form = SubmitTaskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        sub = form.save(commit=False)
        sub.intern = request.user
        sub.task = task
        sub.save()
        task.status = AssignedTask.Status.SUBMITTED
        task.rejection_remark = ""
        task.save()
        messages.success(request, f"Submission for {task.task_id} sent for review.")
        return redirect("tasks")

    counts = get_unread_counts(request.user)
    return render(request, "dashboard/submit_task.html", {
        "task": task,
        "form": form,
        **counts,
    })


@role_required(CustomUser.Role.CONTENT_INTERN, CustomUser.Role.TECH_INTERN)
def raise_ticket(request):
    dept = "CONTENT" if request.user.role == CustomUser.Role.CONTENT_INTERN else "TECH"
    form = TicketForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ticket = form.save(commit=False)
        ticket.raised_by = request.user
        ticket.department = dept
        ticket.save()
        messages.success(request, "Support ticket raised.")
        return redirect("tickets")
    counts = get_unread_counts(request.user)
    return render(request, "dashboard/raise_ticket.html", {"form": form, **counts})


@role_required(CustomUser.Role.CONTENT_INTERN)
def cms_tools(request):
    """Content Management submission tools (syllabus / notes entry, backed by Google Sheets)."""
    counts = get_unread_counts(request.user)
    return render(request, "dashboard/cms_tools.html", {**counts})


# ─── Profile ───────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    profile_form = ProfileUpdateForm(request.POST or None, instance=request.user, prefix="profile")
    password_form = PasswordChangeForm(request.user, request.POST or None, prefix="password")

    if request.method == "POST" and "update_profile" in request.POST and profile_form.is_valid():
        profile_form.save()
        messages.success(request, "Profile updated.")
        return redirect("profile")

    if request.method == "POST" and "change_password" in request.POST and password_form.is_valid():
        user = password_form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Password changed.")
        return redirect("profile")

    counts = get_unread_counts(request.user)
    return render(request, "dashboard/profile.html", {
        "profile_form": profile_form,
        "password_form": password_form,
        **counts,
    })


# ─── Intern ID Lookup (AJAX) ────────────────────────────────────────────────────

@role_required(CustomUser.Role.CONTENT_SUPERVISOR, CustomUser.Role.TECH_SUPERVISOR)
def lookup_intern(request):
    intern_id = request.GET.get("intern_id", "").strip()
    dept_role = CustomUser.Role.CONTENT_INTERN if request.user.role == CustomUser.Role.CONTENT_SUPERVISOR else CustomUser.Role.TECH_INTERN
    try:
        intern = CustomUser.objects.get(intern_id=intern_id, role=dept_role)
        return JsonResponse({
            "found": True,
            "name": intern.get_full_name() or intern.username,
            "college": intern.college_name,
            "department": intern.get_department_display() or "—",
        })
    except CustomUser.DoesNotExist:
        return JsonResponse({"found": False})