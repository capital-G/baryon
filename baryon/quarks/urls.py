from django.urls import path
from django.views.decorators.cache import cache_page

from . import views

urlpatterns = [
    path("", cache_page(1)(views.IndexView.as_view()), name="index"),
    path("quarks", views.QuarksListView.as_view(), name="quarks"),
    path("extensions", views.ExtensionListView.as_view(), name="extensions"),
    path("classes", views.ClassesListView.as_view(), name="classes"),
    path("docs", views.DocsListView.as_view(), name="docs"),
    path("about", cache_page(1)(views.AboutView.as_view()), name="about"),
    # cache this as this has dependencies scanning
    path(
        "project/<str:name>",
        cache_page(0.1)(views.ProjectDetailView.as_view()),
        name="project",
    ),
]
