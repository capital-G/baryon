from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from quarks.serializers import ExtensionViewSet, QuarkViewSet
from rest_framework import permissions, routers

router = routers.DefaultRouter()

router.register("quarks", QuarkViewSet)
router.register("extension", ExtensionViewSet)
# router.register("projects", ProjectViewSet)


# open API stuff
schema_view = get_schema_view(
    openapi.Info(
        title="Quarks API",
        default_version="v1",
        description="Foobar",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="AGPL-3.0 License"),
    ),
    #    url="/api",
    public=True,
    permission_classes=(permissions.AllowAny,),
)
