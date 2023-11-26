import uuid
from pathlib import Path

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _

from .sc.extractor import ProjectRepo as Extractor


class Project(models.Model):
    class ProjectType(models.TextChoices):
        QUARK = "quark", _("Quark")
        EXTENSION = "extension", _("Extension")

    class Formatting(models.TextChoices):
        RST = "rst", _("RST")
        MARKDOWN = "md", _("Markdown")
        RAW = (
            "raw",
            _("Raw"),
        )

    uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        unique=True,
    )

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    first_commit = models.DateTimeField(
        null=True,
        blank=False,
        help_text=_("Datetime of first commit"),
    )

    latest_commit = models.DateTimeField(
        null=True,
        blank=False,
        help_text=_("Datetime of latest commit"),
    )

    project_type = models.CharField(
        max_length=64, null=False, blank=False, choices=ProjectType.choices
    )

    git_url = models.URLField(
        verbose_name=_("URL of git repository"),
        max_length=1024,
        blank=False,
        null=False,
        unique=True,
    )

    name = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        unique=True,
    )

    project_help = models.TextField()

    project_help_formatting = models.CharField(
        max_length=40,
        choices=Formatting.choices,
        help_text=_("Used formatting for text file"),
    )

    # @todo this is deprecated?
    dependencies = models.ManyToManyField(  # type: ignore
        "Project",
        related_name="dependents",
        blank=True,
    )

    def get_dependencies(self) -> models.QuerySet["Project"]:
        dependencies = []

        # try to extract dependencies from quark file
        for d in ["dependencies", "ext_dependency"]:
            dep = self.quark_info.get(d, [])

            if isinstance(dep, str):
                # e.g. 3dj has ext_dependency listed as a string
                dep = [x.strip() for x in dep.split(",")]

            if not isinstance(dep, list):
                return Project.objects.none()

            dependencies.extend(dep)

        if len(dependencies) == 0:
            return Project.objects.none()

        # fuzzy match against dependency names/urls
        query = Q()
        for dependency_name in dependencies:
            query |= Q(git_url__icontains=dependency_name) | Q(
                name__icontains=dependency_name
            )

        return Project.objects.filter(query)

    def get_dependents(self) -> models.QuerySet["Project"]:
        return Project.objects.filter(
            Q(quark_info__dependencies__icontains=self.name)
            | Q(quark_info__ext_dependency___icontains=self.name)
        )

    quark_info = models.JSONField(
        help_text=_("Extracted info from quark file"),
        default=dict,
    )

    def _build_repo_url(self, relative_file_path: Path) -> str:
        return Extractor.build_repo_url_for_file(
            git_url=self.git_url,
            relative_file_path=relative_file_path,
            # does this work?
            default_branch="master",
        )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.project_type})"


class ProjectVersion(models.Model):
    uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        unique=True,
    )

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="versions",
    )

    version_name = models.CharField(
        max_length=1024,
        blank=False,
        null=False,
    )

    release_date = models.DateTimeField(
        help_text=_("Derived from git push"),
    )

    git_hash = models.CharField(
        max_length=100,
        null=True,
        help_text=_("Hash of associated git commit"),
    )

    url = models.URLField(
        help_text=_("Potential URL to release"),
        null=True,
    )

    class Meta:
        ordering = [
            "project",
            "-release_date",
        ]

    def __str__(self) -> str:
        return self.version_name


class ProjectClass(models.Model):
    uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        unique=True,
    )

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    project = models.ForeignKey(
        to=Project,
        on_delete=models.CASCADE,
        related_name="classes",
    )

    file_path = models.CharField(
        max_length=400,
        blank=False,
        null=False,
        help_text=_("Path of file which declares the class"),
    )

    name = models.CharField(
        max_length=400,
        blank=False,
        null=False,
        help_text=_("Name of class"),
    )

    super_class = models.CharField(
        max_length=400,
        null=True,
        blank=True,
        help_text=_("Optional super class"),
    )

    is_extension = models.BooleanField(
        null=False, default=False, help_text=_("Is class extension")
    )

    @property
    def repo_url(self) -> str:
        return self.project._build_repo_url(
            relative_file_path=Path(self.file_path),
        )

    class Meta:
        ordering = [
            "project",
            "is_extension",
            "name",
        ]

    def __str__(self) -> str:
        return self.name


# DOCS_STORAGE = FileSystemStorage("sc_docs/")


class ProjectDoc(models.Model):
    uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        unique=True,
    )

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="docs",
    )

    html_file = models.FileField(
        upload_to="sc_docs",
        # storage=DOCS_STORAGE,
        blank=False,
        null=False,
    )

    source_path = models.CharField(
        max_length=512,
        help_text=_("Source code path of help file in repository"),
    )

    @property
    def repo_url(self) -> str:
        return self.project._build_repo_url(
            relative_file_path=Path(self.source_path),
        )

    class Meta:
        ordering = [
            "project",
            "source_path",
        ]

    def __str__(self) -> str:
        return self.source_path
