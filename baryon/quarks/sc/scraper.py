import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import yaml

from ..models import Project, ProjectClass, ProjectDoc, ProjectVersion
from .extractor import ProjectRepo, ProjectType, ReadmeFormatting

logger = logging.getLogger(__name__)


class ProjectScraper:
    QUARKS_TXT_LIST_URL = "https://raw.githubusercontent.com/supercollider-quarks/quarks/master/directory.txt"
    QUARKS_TXT_REGEX = re.compile(
        r"(?P<name>[A-Za-z-_0-9\.]*)=(?P<url>[^@\n]*)@?(?P<tag>.*)"
    )
    EXTENSION_YAML_PATH = (
        Path(__file__).parent.joinpath("../../extensions.yml").resolve()
    )

    REPO_PATH = Path(__file__).parent.joinpath("../repos").resolve()

    def __init__(self, num_instances: int = 8) -> None:
        self.num_instances = num_instances
        self.queue: asyncio.Queue[Optional[ProjectRepo]] = asyncio.Queue()

    async def _fetch_quark_repos(self) -> List[ProjectRepo]:
        quark_repos: List[ProjectRepo] = []
        async with aiohttp.ClientSession() as s:
            async with s.get(self.QUARKS_TXT_LIST_URL) as r:
                for match in self.QUARKS_TXT_REGEX.finditer(await r.text()):
                    match_dict = match.groupdict()
                    quark_repos.append(
                        ProjectRepo(
                            project_type=ProjectType.QUARK,
                            name=match_dict["name"],
                            url=match_dict["url"],
                            repo_path=self.REPO_PATH.joinpath(match_dict["name"]),
                            default_tag=match_dict["tag"]
                            if match_dict["tag"]
                            else None,
                        )
                    )
        # @todo check quarks in db are not listed in txt?
        return quark_repos

    @staticmethod
    def _convert_formatting(f: ReadmeFormatting) -> Project.Formatting:
        match f:
            case ReadmeFormatting.MARKDOWN:
                return Project.Formatting.MARKDOWN
            case ReadmeFormatting.RST:
                return Project.Formatting.RST
            case ReadmeFormatting.RAW:
                return Project.Formatting.RAW
            case ReadmeFormatting.TXT:
                return Project.Formatting.RAW
            case _:
                raise Exception()

    @staticmethod
    def _convert_project_type(t: ProjectType) -> Project.ProjectType:
        match t:
            case ProjectType.QUARK:
                return Project.ProjectType.QUARK
            case _:
                return Project.ProjectType.EXTENSION

    async def _worker(self, worker_number: int):
        while True:
            quark = await self.queue.get()
            if quark is None:
                logger.info(f"Worker {worker_number} will shut down")
                self.queue.task_done()
                break

            logger.info(f"Worker {worker_number} starts on {quark}")

            project, created = await Project.objects.aget_or_create(
                name=quark.name,
                git_url=quark.url,
                project_type=self._convert_project_type(quark.project_type),
            )

            try:
                await quark.init_repo()
                await quark.update_repo()
                project.default_branch = await quark.get_default_branch()

                first_commit = await quark.get_first_commit()
                project.first_commit = first_commit.date

                latest_commit = await quark.get_current_commit()
                project.latest_commit = latest_commit.date

                tags = await quark.get_git_tags()

                for tag in tags:
                    if tag.tag is None:
                        continue
                    await ProjectVersion.objects.aget_or_create(
                        project=project,
                        version_name=tag.tag,
                        release_date=tag.date,
                        git_hash=tag.hash,
                    )

                for sc_class in quark.get_classes():
                    await ProjectClass.objects.aupdate_or_create(
                        # identifier
                        project=project,
                        name=sc_class.name,
                        # to be updated
                        defaults={
                            "file_path": str(
                                sc_class.file_path.relative_to(quark.repo_path)
                            ),
                            "super_class": sc_class.super_class,
                            "is_extension": sc_class.is_extension,
                        },
                    )

                if readme := quark.get_readme():
                    logger.debug(f"Found readme for {quark}")
                    project.project_help = readme.text
                    project.project_help_formatting = self._convert_formatting(
                        readme.formatting
                    )

                project.quark_info = await quark.extract_quark_info()

                for help_source_path in quark.find_doc_paths():
                    doc_files = await quark.build_docs(help_source_path)
                    quark.fix_doc_links(doc_files)
                    for doc in doc_files:
                        if doc.html_path is None:
                            continue
                        await ProjectDoc.objects.aupdate_or_create(
                            project=project,
                            source_path=doc.source_path.relative_to(quark.repo_path),
                            defaults={
                                "html_file": str(
                                    doc.html_path.relative_to(
                                        ProjectRepo.SCDOC_TARGET_PATH.joinpath(
                                            ".."
                                        ).resolve()
                                    )
                                ),
                            },
                        )
            except TimeoutError as e:
                logger.error(f"Found error on {quark}: {e}")
            finally:
                await project.asave()
                self.queue.task_done()
                logger.info(f"Finished working on {quark}")

    async def scrape_quarks(self, limit: Optional[int] = None):
        logger.info(f"Start scraping quarks with {self.num_instances} instances")

        for quark_num, quark_entry in enumerate(await self._fetch_quark_repos()):
            if limit:
                if quark_num >= limit:
                    break
            await self.queue.put(quark_entry)

        # Create worker tasks to process the queue concurrently.
        workers = [
            asyncio.create_task(self._worker(i)) for i in range(self.num_instances)
        ]

        # Wait until the queue is empty
        await self.queue.join()

        # Put None in the queue to signal workers to stop
        for _ in range(self.num_instances):
            await self.queue.put(None)

        # wait for shutdown of workers
        await asyncio.gather(*workers)

    async def _fetch_extensions(self) -> List[ProjectRepo]:
        with open(self.EXTENSION_YAML_PATH, "r") as f:
            extensions_yaml: Dict = yaml.safe_load(f)
        extensions: List[ProjectRepo] = []
        raw_extensions = extensions_yaml.get("extensions", [])
        for raw_extension in raw_extensions:
            try:
                extensions.append(
                    ProjectRepo(
                        project_type=ProjectType.EXTENSION,
                        repo_path=self.REPO_PATH.joinpath(raw_extension["name"]),
                        **raw_extension,
                    )
                )
            except Exception as e:
                print(e)
        return extensions

    async def scrape_extensions(self, limit: Optional[int] = None):
        logger.info(f"Start scraping quarks with {self.num_instances} instances")

        for num, extension_entry in enumerate(await self._fetch_extensions()):
            if limit:
                if num >= limit:
                    break
            await self.queue.put(extension_entry)

        # Create worker tasks to process the queue concurrently.
        workers = [
            asyncio.create_task(self._worker(i)) for i in range(self.num_instances)
        ]

        # Wait until the queue is empty
        await self.queue.join()

        # Put None in the queue to signal workers to stop
        for _ in range(self.num_instances):
            await self.queue.put(None)

        # wait for shutdown of workers
        await asyncio.gather(*workers)
