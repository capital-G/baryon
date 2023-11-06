from typing import Optional

import django_filters
from rest_framework import filters, serializers, viewsets

from .models import Project, ProjectClass, ProjectDoc, ProjectVersion


class ProjectVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectVersion
        fields = [
            "version_name",
            "release_date",
        ]


class ProjectClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectClass
        fields = [
            "file_path",
            "name",
            "super_class",
            "is_extension",
        ]


class ProjectDocSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDoc
        fields = [
            "html_file",
            "source_path",
        ]


class ProjectDetailSerializer(serializers.HyperlinkedModelSerializer):
    versions = ProjectVersionSerializer(many=True, read_only=True)
    classes = ProjectClassSerializer(many=True, read_only=True)
    docs = ProjectDocSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "uuid",
            "git_url",
            "name",
            "quark_info",
            "project_type",
            "versions",
            "classes",
            "docs",
        ]


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    summary = serializers.SerializerMethodField()

    def get_summary(self, obj: Project) -> Optional[str]:
        return obj.quark_info.get("summary", None)

    class Meta:
        model = Project
        fields = [
            "git_url",
            "name",
            "summary",
            "latest_commit",
        ]


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all()

    lookup_field = "name"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProjectDetailSerializer
        return ProjectSerializer

    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
    ]
    search_fields = ["name"]


class QuarkViewSet(ProjectViewSet):
    queryset = Project.objects.filter(project_type=Project.ProjectType.QUARK)


class ExtensionViewSet(ProjectViewSet):
    queryset = Project.objects.filter(project_type=Project.ProjectType.EXTENSION)
