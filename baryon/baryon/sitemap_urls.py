from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.contrib.sitemaps.views import sitemap
from django.urls import path, reverse
from django.views.decorators.cache import cache_page

from quarks.models import Project, ProjectDoc


class StaticViewSitemap(Sitemap):
    priority = 0.4
    changefreq = "daily"

    def items(self):
        return ["index", "quarks", "classes", "about"]

    def location(self, item):
        return reverse(item)


urlpatterns = [
    path(
        "sitemap.xml",
        cache_page(4 * 60 * 60)(sitemap),
        {
            "sitemaps": {
                "projects": GenericSitemap(
                    info_dict={
                        "queryset": Project.objects.all(),  # type: ignore
                        "date_filed": "latest_commit",
                    },
                    priority=0.7,
                    changefreq="daily",
                ),
                "docs": GenericSitemap(
                    info_dict={
                        "queryset": ProjectDoc.objects.all(),  # type: ignore
                        "date_filed": "modified_date",
                    },
                    priority=0.5,
                    changefreq="daily",
                ),
                "static": StaticViewSitemap(),
            }
        },
    ),
]
