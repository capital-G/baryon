from django.contrib import admin

from .models import Project, ProjectClass, ProjectDoc, ProjectVersion


class ProjectClassInline(admin.TabularInline):
    model = ProjectClass
    extra = 0


class ProjectVersionInline(admin.TabularInline):
    model = ProjectVersion
    extra = 0


class ProjectDocInline(admin.TabularInline):
    model = ProjectDoc
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "git_url",
        "project_type",
    ]

    search_fields = [
        "name",
        "git_url",
    ]

    list_filter = ["project_type"]

    autocomplete_fields = [
        "dependencies",
    ]

    readonly_fields = ["uuid"]

    inlines = [
        ProjectVersionInline,
        ProjectClassInline,
        ProjectDocInline,
    ]
