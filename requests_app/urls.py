from django.urls import path

from .views import (
    EmployeeCreateView,
    EmployeeListView,
    HomeRedirectView,
    RequestAssigneeUpdateView,
    RequestCreateView,
    RequestListView,
    RequestStatusUpdateView,
)

app_name = "requests_app"

urlpatterns = [
    path("", HomeRedirectView.as_view(), name="home"),
    path("requests/", RequestListView.as_view(), name="request_list"),
    path("requests/create/", RequestCreateView.as_view(), name="request_create"),
    path(
        "requests/<int:pk>/status/",
        RequestStatusUpdateView.as_view(),
        name="request_status_update",
    ),
    path(
        "requests/<int:pk>/assignee/",
        RequestAssigneeUpdateView.as_view(),
        name="request_assignee_update",
    ),
    path("employees/", EmployeeListView.as_view(), name="employee_list"),
    path("employees/create/", EmployeeCreateView.as_view(), name="employee_create"),
]
