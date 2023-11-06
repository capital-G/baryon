import django_filters
from rest_framework import filters, serializers, viewsets

from .models import Project, ProjectClass, ProjectVersion


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


class ProjectDetailSerializer(serializers.HyperlinkedModelSerializer):
    versions = ProjectVersionSerializer(many=True, read_only=True)
    classes = ProjectClassSerializer(many=True, read_only=True)

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
        ]


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = [
            "uuid",
            "git_url",
            "name",
            "quark_info",
        ]


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all()

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
