from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Department, Employee, Position, Request


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("name",)


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ("name",)


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ("full_name", "department", "position", "is_active")


class RequestCreateForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ("number", "author", "assignee", "description", "due_date")
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data["due_date"]
        if due_date < timezone.localdate():
            raise ValidationError("Срок выполнения не может быть раньше текущей даты.")
        return due_date


class RequestStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Request.Status.choices, label="Статус")

    def __init__(self, *args, request_instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_instance = request_instance

        if request_instance is not None:
            self.fields["status"].initial = request_instance.status

    def clean_status(self):
        new_status = self.cleaned_data["status"]
        if self.request_instance is None:
            return new_status

        if new_status == self.request_instance.status:
            return new_status

        if not self.request_instance.can_transition_to(new_status):
            raise ValidationError("Недопустимый переход между статусами.")

        return new_status


class RequestAssigneeForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ("assignee",)


class RequestFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[("", "Все статусы"), *Request.Status.choices],
        required=False,
        label="Статус",
    )
    assignee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        empty_label="Все исполнители",
        label="Исполнитель",
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="Все подразделения",
        label="Подразделение",
    )
    is_overdue = forms.BooleanField(required=False, label="Только просроченные")
