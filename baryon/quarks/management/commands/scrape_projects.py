import asyncio
from argparse import ArgumentParser
from typing import Optional

from django.core.management.base import BaseCommand  # type: ignore

from quarks.sc.scraper import ProjectScraper


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--limit",
            help="Limit the number of quarks to be scraped - useful for testing",
            type=int,
        )

        parser.add_argument(
            "-e",
            "--no-extensions",
            action="store_false",
            help="Omit extension scraping",
        )

        parser.add_argument(
            "-q",
            "--no-quarks",
            action="store_false",
            help="Omit quark scraping",
        )

    async def scrape_extensions(self, limit: Optional[int] = None):
        scraper = ProjectScraper()
        await scraper.scrape_extensions(limit)

    async def scrape_quarks(self, limit: Optional[int] = None):
        scraper = ProjectScraper()
        await scraper.scrape_quarks(limit)

    def handle(self, *args, **options):
        if options.get("--no-extensions", True):
            asyncio.run(self.scrape_extensions(limit=options.get("limit")))

        if options.get("--no-quarks", True):
            asyncio.run(self.scrape_quarks(limit=options.get("limit")))
