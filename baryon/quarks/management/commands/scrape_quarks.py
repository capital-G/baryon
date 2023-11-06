import asyncio
from pathlib import Path

from django.core.management.base import BaseCommand  # type: ignore

from quarks.sc.scraper import ProjectRepo, ProjectScraper, ProjectType


class Command(BaseCommand):
    async def foo(self):
        project = ProjectRepo(
            project_type=ProjectType.QUARK,
            name="atk-sc3",
            url="http://",
            repo_path=Path("/Users/scheiba/github/sc-quarks/baryon/repos/AlgaLib"),
            default_tag=None,
        )
        await project.init_repo()

        print(project.get_readme())
        print(await project.extract_quark_info())
        print("Found classes", [x.name for x in project.get_classes()])
        # print(await project.build_docs())
        print("Finished")

    async def bar(self):
        scraper = ProjectScraper()
        await scraper.scrape_quarks()

    def handle(self, *args, **kwargs):
        asyncio.run(self.bar())
