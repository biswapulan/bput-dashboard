from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard_home, name="dashboard-home"),
    path("dashboard/admin/", views.admin_dashboard, name="admin-dashboard"),
    path("dashboard/content-supervisor/", views.content_supervisor_dashboard, name="content-supervisor-dashboard"),
    path("dashboard/tech-supervisor/", views.tech_supervisor_dashboard, name="tech-supervisor-dashboard"),
    path("dashboard/content-intern/", views.content_intern_dashboard, name="content-intern-dashboard"),
    path("dashboard/tech-intern/", views.tech_intern_dashboard, name="tech-intern-dashboard"),
    path("dashboard/submissions/<int:submission_id>/<str:decision>/", views.review_submission, name="review-submission"),
    path("dashboard/tickets/<int:ticket_id>/resolve/", views.resolve_ticket, name="resolve-ticket"),
]
