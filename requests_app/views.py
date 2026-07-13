from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, RedirectView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView

from .forms import (
    EmployeeForm,
    RequestAssigneeForm,
    RequestCreateForm,
    RequestFilterForm,
    RequestStatusForm,
)
from .models import Employee, Request


class HomeRedirectView(RedirectView):
    """Перенаправляет с главной страницы на список заявок."""

    pattern_name = "requests_app:request_list"
    permanent = False


class RequestListView(ListView):
    """Показывает список заявок и применяет фильтры из GET-параметров."""

    model = Request
    template_name = "requests_app/request_list.html"
    context_object_name = "requests"

    def get_queryset(self):
        """Возвращает queryset заявок с учетом выбранных фильтров."""

        queryset = Request.objects.all()

        self.filter_form = RequestFilterForm(self.request.GET or None)
        if not self.filter_form.is_valid():
            return queryset

        status = self.filter_form.cleaned_data.get("status")
        assignee = self.filter_form.cleaned_data.get("assignee")
        department = self.filter_form.cleaned_data.get("department")
        is_overdue = self.filter_form.cleaned_data.get("is_overdue")

        if status:
            queryset = queryset.filter(status=status)
        if assignee:
            queryset = queryset.filter(assignee=assignee)
        if department:
            queryset = queryset.filter(assignee__department=department)
        if is_overdue:
            queryset = queryset.filter(due_date__lt=timezone.localdate()).exclude(
                status=Request.Status.DONE
            )

        return queryset

    def get_context_data(self, **kwargs):
        """Добавляет форму фильтров в контекст шаблона."""

        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class RequestCreateView(CreateView):
    """Создает новую заявку через форму RequestCreateForm."""

    model = Request
    form_class = RequestCreateForm
    template_name = "requests_app/request_form.html"
    success_url = reverse_lazy("requests_app:request_list")

    def form_valid(self, form):
        """Сохраняет заявку и показывает сообщение об успешном создании."""

        messages.success(self.request, "Заявка успешно создана.")
        return super().form_valid(form)


class RequestStatusUpdateView(SingleObjectMixin, FormView):
    """Меняет статус заявки с проверкой допустимого перехода."""

    model = Request
    form_class = RequestStatusForm
    template_name = "requests_app/request_status_form.html"
    success_url = reverse_lazy("requests_app:request_list")
    context_object_name = "request_instance"

    def dispatch(self, request, *args, **kwargs):
        """Находит заявку до обработки GET или POST запроса."""

        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Передает текущую заявку в форму смены статуса."""

        kwargs = super().get_form_kwargs()
        kwargs["request_instance"] = self.object
        return kwargs

    def form_valid(self, form):
        """Применяет бизнес-правило перехода статуса и сохраняет заявку."""

        self.object.transition_to(form.cleaned_data["status"])
        self.object.save(update_fields=["status"])
        messages.success(self.request, "Статус заявки обновлён.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Добавляет текущую заявку в контекст шаблона."""

        context = super().get_context_data(**kwargs)
        context["request_instance"] = self.object
        return context


class RequestAssigneeUpdateView(UpdateView):
    """Меняет исполнителя существующей заявки."""

    model = Request
    form_class = RequestAssigneeForm
    template_name = "requests_app/request_assignee_form.html"
    success_url = reverse_lazy("requests_app:request_list")
    context_object_name = "request_instance"

    def form_valid(self, form):
        """Сохраняет нового исполнителя и показывает сообщение об успехе."""

        messages.success(self.request, "Исполнитель заявки обновлён.")
        return super().form_valid(form)


class EmployeeListView(ListView):
    """Показывает список сотрудников с подразделениями и должностями."""

    model = Employee
    template_name = "requests_app/employee_list.html"
    context_object_name = "employees"


class EmployeeCreateView(CreateView):
    """Создает нового сотрудника через форму EmployeeForm."""

    model = Employee
    form_class = EmployeeForm
    template_name = "requests_app/employee_form.html"
    success_url = reverse_lazy("requests_app:employee_list")

    def form_valid(self, form):
        """Сохраняет сотрудника и показывает сообщение об успешном создании."""

        messages.success(self.request, "Сотрудник успешно создан.")
        return super().form_valid(form)
