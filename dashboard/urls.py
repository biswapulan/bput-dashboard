from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_home, name="dashboard-home"),
    path("tasks/", views.tasks, name="tasks"),
    path("tickets/", views.tickets, name="tickets"),
    path("submissions/", views.submissions, name="submissions"),
    path("announcements/", views.announcements, name="announcements-short"),

    # Admin
    path("dashboard/admin/", views.admin_dashboard, name="admin-dashboard"),
    path("dashboard/create-intern/", views.create_intern, name="create-intern"),
    path("dashboard/users/", views.user_management, name="user-management"),
    path("dashboard/users/<int:user_id>/delete/", views.delete_user, name="delete-user"),
    path("dashboard/attendance/", views.admin_attendance, name="admin-attendance"),
    path("dashboard/archive/", views.admin_archive, name="admin-archive"),

    # Announcements (all roles)
    path("dashboard/announcements/", views.announcements, name="announcements"),
    path("dashboard/announcements/<str:ann_id>/delete/", views.delete_announcement, name="delete-announcement"),

    # Supervisor
    path("dashboard/supervisor/", views.supervisor_dashboard, name="supervisor-dashboard"),
    path("dashboard/supervisor/assign-task/", views.assign_task, name="assign-task"),
    path("dashboard/supervisor/tasks/<str:task_id>/<str:decision>/", views.review_task, name="review-task"),
    path("dashboard/supervisor/tickets/<str:token_id>/resolve/", views.resolve_ticket, name="resolve-ticket"),
    path("dashboard/supervisor/archive/", views.supervisor_archive, name="supervisor-archive"),
    path("dashboard/supervisor/lookup-intern/", views.lookup_intern, name="lookup-intern"),
    path("dashboard/supervisor/send-message/", views.supervisor_send_message, name="supervisor-send-message"),

    # Intern
    path("dashboard/intern/", views.intern_dashboard, name="intern-dashboard"),
    path("dashboard/intern/attendance/", views.intern_attendance, name="intern-attendance"),
    path("dashboard/intern/tasks/<str:task_id>/submit/", views.submit_task, name="submit-task"),
    path("dashboard/intern/raise-ticket/", views.raise_ticket, name="raise-ticket"),
    path("dashboard/intern/cms/", views.cms_tools, name="cms-tools"),
    path("dashboard/intern/messages/", views.intern_messages, name="intern-messages"),

    # Profile
    path("profile/", views.profile, name="profile"),
]
