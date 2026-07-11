from django.contrib import admin

from .models import Department, Employee, Position, Request


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "department", "position", "is_active")
    list_filter = ("department", "position", "is_active")
    search_fields = ("full_name",)
    ordering = ("full_name",)


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "number",
        "status",
        "author",
        "assignee",
        "due_date",
        "created_at",
        "is_overdue",
    )
    list_filter = ("status", "assignee", "author", "due_date")
    search_fields = (
        "number",
        "description",
        "author__full_name",
        "assignee__full_name",
    )
    autocomplete_fields = ("author", "assignee")
    date_hierarchy = "created_at"
    ordering = ("due_date", "number")

    @admin.display(boolean=True, description="Просрочена")
    def is_overdue(self, obj):
        return obj.is_overdue
