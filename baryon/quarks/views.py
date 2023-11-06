from typing import Any, List

from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .models import Project, ProjectClass


def index(request: HttpRequest):
    num_of_quarks = 5
    return render(
        request,
        "index.html",
        context={
            "random_quarks": Project.objects.order_by("?")[0:num_of_quarks],
            "latest_quarks": Project.objects.order_by("-first_commit")[0:num_of_quarks],
            "latest_updates": Project.objects.order_by("-latest_commit")[
                0:num_of_quarks
            ],
        },
    )


def about(request: HttpRequest):
    return render(request, "about.html")


class ClassesListView(ListView):
    paginate_by = 24
    model = ProjectClass
    context_object_name = "classes"

    def get_template_names(self) -> List[str]:
        if self.request.htmx:  # type: ignore
            return ["partials/class-list.html"]
        return ["classes.html"]

    def get_queryset(self) -> QuerySet[ProjectClass]:
        qs: QuerySet[ProjectClass] = super().get_queryset()  # type: ignore
        # qs = qs.filter(is_extension=False)
        if search_term := self.request.GET.get("search"):
            qs = qs.filter(name__icontains=search_term)
        return qs


class ProjectListView(ListView):
    paginate_by = 24
    model = Project
    context_object_name = "projects"

    def get_template_names(self) -> List[str]:
        if self.request.htmx:  # type: ignore
            return ["partials/projects-list.html"]
        return ["projects.html"]

    def get_queryset(self) -> QuerySet[Project]:
        qs: QuerySet[Project] = super().get_queryset()  # type: ignore
        if search_term := self.request.GET.get("search"):
            qs = qs.filter(
                Q(name__icontains=search_term)
                | Q(quark_info__summary__icontains=search_term)
                | Q(project_help__icontains=search_term)
            )
        return qs


class QuarksListView(ProjectListView):
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return {**super().get_context_data(**kwargs), "project_type": "Quarks"}

    def get_queryset(self) -> QuerySet[Project]:
        return super().get_queryset().filter(project_type=Project.ProjectType.QUARK)


class ExtensionListView(ProjectListView):
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return {**super().get_context_data(**kwargs), "project_type": "Extensions"}

    def get_queryset(self) -> QuerySet[Project]:
        return super().get_queryset().filter(project_type=Project.ProjectType.EXTENSION)


class ProjectDetailView(DetailView):
    model = Project
    context_object_name = "project"
    template_name = "project.html"

    def get_object(self, *args, **kwargs) -> Project:
        return Project.objects.get(name=self.kwargs.get("name"))
