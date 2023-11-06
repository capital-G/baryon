from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers

from quarks.serializers import ExtensionViewSet, QuarkViewSet

router = routers.DefaultRouter()

router.register("quarks", QuarkViewSet)
router.register("extension", ExtensionViewSet)


schema_view = get_schema_view(
    openapi.Info(
        title="Baryon API",
        default_version="v1",
        description="REST API for Baryon",
        license=openapi.License(name="AGPL-3.0 License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
