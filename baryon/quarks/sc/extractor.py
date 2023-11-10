import asyncio
import dataclasses
import enum
import json
import logging
import os
import re
import shutil
import tempfile
from asyncio.subprocess import PIPE
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import chardet
import pytz

logger = logging.getLogger(__name__)


class RepoUnavailable(Exception):
    pass


class ProjectType(enum.Enum):
    QUARK = "quark"
    EXTENSION = "extension"


@dataclasses.dataclass
class CommitInfo:
    hash: str
    date: datetime
    tag: Optional[str] = None


@dataclasses.dataclass
class SclangClass:
    file_path: Path
    name: str
    super_class: Optional[str] = None
    is_extension: bool = False


class ReadmeFormatting(enum.Enum):
    RST = ".rst"
    MARKDOWN = ".md"
    RAW = ""
    TXT = ".txt"


@dataclasses.dataclass
class Readme:
    file_path: Path
    formatting: ReadmeFormatting
    text: str


@dataclasses.dataclass
class HelpFile:
    source_path: Path
    html_path: Optional[Path]


class ProjectRepo:
    """

    .. note::

        Keep this independent of Django/DB so it can be reused in other projects
        and tested without Django.


    """

    GIT_COMMIT_DATE_REGEX = re.compile(r"Date:\s+(?P<date>.*)\n")
    SCLANG_CLASS_DECLARATION_REGEX = re.compile(
        r"^\s*(?P<extension>\+?)\s*(?P<name>[A-Z]+[A-z]*)\s*(\:\s*(?P<super>[A-Z]+[A-z]*))?\s*{",
        re.MULTILINE,
    )
    # not used
    SCLANG_CLASS_USAGE_REGEX = re.compile(
        r"[\t\s]*(?<![A-za-z])(?P<class>[A-Z]+[A-Za-z0-9]*)[\.\(]", re.MULTILINE
    )

    SCLANG_PATH = os.environ.get("SCLANG_PATH", "sclang")

    # attention - hardcoded path!
    SCDOC_TARGET_PATH = Path(__file__).parent.joinpath("../../media/sc_docs").resolve()

    def __init__(
        self,
        project_type: ProjectType,
        name: str,
        url: str,
        repo_path: Path,
        default_tag: Optional[str],
    ) -> None:
        self.project_type = project_type
        self.name = name
        self.url = url
        self.repo_path = repo_path
        self.default_tag = default_tag

    @classmethod
    async def new_repo(cls, **kwargs):
        project = cls(**kwargs)
        await project.init_repo()
        return project

    async def git(self, *args, cwd: Optional[Path] = None) -> str:
        cwd = cwd if cwd else self.repo_path
        git_process = await asyncio.create_subprocess_exec(
            "git", *args, cwd=cwd, stdout=PIPE, stderr=PIPE
        )
        stdout, stderr = await git_process.communicate()
        # assert git_process.returncode == 0
        return stdout.decode()

    async def get_git_tags(self) -> List[CommitInfo]:
        raw_tag_info = await self.git("show-ref", "--tags")
        git_tags: List[CommitInfo] = []
        for git_tag_info in raw_tag_info.split("\n"):
            if git_tag_info == "":
                continue
            commit_hash, tag = git_tag_info.split(" ")
            commit_info = await self.extract_commit_info(commit_hash)
            commit_info.tag = tag.replace("refs/tags/", "")
            git_tags.append(commit_info)
        return git_tags

    async def get_current_commit(self) -> CommitInfo:
        current_commit = (
            await self.git(
                "--no-pager",
                "log",
                "--format=%H",
                "-n",
                "1",
            )
        ).strip()
        return await self.extract_commit_info(current_commit)

    async def get_first_commit(self) -> CommitInfo:
        first_commit_hash = (
            (
                await self.git(
                    "--no-pager",
                    "log",
                    "--format=%H",
                )
            )
            .strip()
            .split("\n")[-1]
        )
        return await self.extract_commit_info(first_commit_hash)

    async def extract_commit_info(self, commit_hash: str) -> CommitInfo:
        # only time for now - show does not offer nice formatting
        raw_commit_epoch = await self.git(
            "--no-pager",
            "log",
            "--decorate=short",
            "--format=%ct",
            "-n",
            "1",
            commit_hash,
        )
        return CommitInfo(
            hash=commit_hash,
            date=datetime.fromtimestamp(
                float(raw_commit_epoch),
                tz=pytz.utc,
            ),
        )

    async def update_repo(self):
        logger.debug(f"Pull repository {self}")
        await self.git("pull")

    def get_readme(self) -> Optional[Readme]:
        readme_candidates: List[Path] = []
        readme_type: ReadmeFormatting = ReadmeFormatting.MARKDOWN
        # list is used as a priority search
        for ext in [
            ReadmeFormatting.MARKDOWN,
            ReadmeFormatting.RST,
            ReadmeFormatting.RAW,
            ReadmeFormatting.TXT,
        ]:
            # glob is case sensitive (future self: python 3.12 fixes this)
            # therefore we use walk (Path.walk is also introduced in 3.12)
            # @todo skip hidden files/folders such as .git
            for folder, _, file_names in os.walk(self.repo_path):
                for file_name in file_names:
                    if file_name.lower() == f"readme{ext.value.lower()}":
                        readme_candidates.append(Path(folder).joinpath(file_name))
                        readme_type = ext
                        break

        if len(readme_candidates) == 0:
            logger.info(f"Could not find a README file for {self}")
            return None

        readme_file_path = readme_candidates[0]
        try:
            with readme_file_path.open("rb") as f:
                file_content = f.read()
                try:
                    text = file_content.decode()
                except UnicodeDecodeError:
                    encodings = chardet.detect(file_content)
                    text = file_content.decode(
                        encoding=encodings["encoding"] or "utf-8", errors="replace"
                    )
                return Readme(
                    file_path=readme_file_path,
                    formatting=readme_type,
                    text=text,
                )
        except Exception as e:
            logger.error(f"Failed to fetch README for {self}: {e}")
            return None

    async def _sclang(self, *args: str, env: Optional[Dict[str, str]] = None) -> str:
        cmd = f"{self.SCLANG_PATH} -i foo {' '.join(args)}"
        # print(f"sc cmd is {cmd} with env {env}")
        if env:
            env = {
                # it is essential to add the default env variables, otherwise boost will throw an exception
                **os.environ.copy(),
                **env,
            }
        # -i foo sets the interpreter - this is somehow necessary
        sclang_process = await asyncio.create_subprocess_shell(
            cmd, stdout=PIPE, stderr=PIPE, env=env
        )

        # # see https://stackoverflow.com/a/42643949/3475778
        task = asyncio.Task(sclang_process.communicate())
        done, pending = await asyncio.wait(
            [task],
            timeout=30,
        )
        if pending:
            print(f"timeout for {self}!", task._state)
            # @todo kill process!
            sclang_process.terminate()
            raise TimeoutError()
            # exception!
        stdout, stderr = await task
        if stderr:
            logger.error(f"Stderr on {cmd}: {stderr.decode()}")
        # assert git_process.returncode == 0
        return stdout.decode()

    async def extract_quark_info(self) -> Dict[str, Any]:
        quark_file_paths = list(self.repo_path.glob("*.quark"))
        if len(quark_file_paths) == 0:
            # @todo raise exception
            logger.error(f"Could not find a quark file for {self}")
            return {}
        quark_file_path = quark_file_paths[0]

        with tempfile.NamedTemporaryFile(
            "r", suffix=f"_sc_quark_{self.name}.json"
        ) as f:
            quark_info_cmd = await self._sclang(
                str(Path(__file__).parent.joinpath("quarkToJson.scd").resolve()),
                env={
                    "QUARK_FILE": str(quark_file_path.absolute()),
                    "QUARK_JSON_FILE": f.name,
                },
            )
            j = json.load(f)

        return j

    async def build_docs(self) -> List[HelpFile]:
        help_source_path = self.repo_path
        if self.repo_path.joinpath("HelpSource").exists():
            help_source_path = help_source_path.joinpath("HelpSource")

        # in order to create a namespace for the docs (so classes with the same name do not clash)
        # it is necessary to create a directory which wraps the schelp files
        # in order to be more stateless this is a temp dir which deletes after the execution
        #
        # another approach was to modify the "ScDocEntry.destPath" within sclang
        # but this is a read-only attribute
        with tempfile.TemporaryDirectory(f"baryon_{self.name}") as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(help_source_path, temp_path.joinpath(self.name))

            quark_info_cmd = await self._sclang(
                str(Path(__file__).parent.joinpath("buildDocs.scd").resolve()),
                env={
                    # parent to create an additional layer for the namespace :)
                    "QUARK_HELP_SOURCE_PATH": str(temp_path),
                    # "QUARK_HELP_SOURCE_FILES": ",".join([str(x.relative_to(namespace_help_source_path.parent)) for x in help_file_paths]),
                    "QUARK_HELP_TARGET_PATH": str(self.SCDOC_TARGET_PATH.absolute()),
                },
            )

            logger.debug(f"Doc build log for {self}: {quark_info_cmd}")

        help_files: List[HelpFile] = []
        doc_name_space_dir = self.SCDOC_TARGET_PATH.joinpath(self.name)
        for dir_name, _, filenames in os.walk(doc_name_space_dir):
            Path(dir_name)
            # html_path = self.SCDOC_TARGET_PATH.joinpath(help_file_path.relative_to(namespace_help_source_path.parent).with_suffix(".html"))
            for filename in filenames:
                # only index html files
                if not filename.endswith(".html"):
                    continue

                html_file = Path(dir_name).joinpath(filename)
                assert html_file.is_file()  # sanity check

                # removes namespace wrapper dir
                relative_path = html_file.relative_to(doc_name_space_dir)
                source_file_path = help_source_path.joinpath(
                    Path(str(relative_path).replace(".html", ".schelp"))
                )
                assert (
                    source_file_path.is_file()
                )  # every html file needs to origin in a sc help file

                help_files.append(
                    HelpFile(source_path=source_file_path, html_path=html_file)
                )

        return help_files

    def get_classes(self) -> List[SclangClass]:
        sclang_classes: List[SclangClass] = []

        sc_files: List[Path] = []
        for pattern in ["**/*.sc", "*.sc"]:
            sc_files.extend(self.repo_path.glob(pattern))

        if len(sc_files) == 0:
            logger.error(f"{self} does not contain any sc files!")

        for sc_file in sc_files:
            text: str
            sc_file_path = self.repo_path.joinpath(sc_file)

            # @todo use chardet to guess encoding
            with open(sc_file_path, "rb") as f:
                file_content = f.read()
                encodings = chardet.detect(file_content)
                text = file_content.decode(encoding=encodings["encoding"] or "utf-8")
            for match in self.SCLANG_CLASS_DECLARATION_REGEX.finditer(text):
                match_dict = match.groupdict()
                sclang_classes.append(
                    SclangClass(
                        file_path=sc_file_path,
                        name=match_dict["name"],
                        super_class=match_dict.get("super", None),
                        is_extension=match_dict.get("extension", "") != "",
                    )
                )
        logger.debug(f"Extracted {len(sclang_classes)} classes from {self}")
        return sclang_classes

    async def init_repo(self):
        # @todo split this into two classes? Pre-Cloned and Post-Cloned?
        # this would result in more code but in better type checking
        if not self.repo_path.exists():
            logger.debug(
                f"Found new repo - clone repository {self} to {self.repo_path}"
            )
            await self.git("clone", self.url, str(self.repo_path), cwd=Path.cwd())
        if not self.repo_path.exists():
            raise RepoUnavailable()

    def __str__(self) -> str:
        return f"{self.name} ({self.url})"


async def foo():
    project = ProjectRepo(
        project_type=ProjectType.QUARK,
        name="atk-sc3",
        url="https://github.com/vitreo12/AlgaLib.git",
        repo_path=Path("/Users/scheiba/github/sc-quarks/baryon/repos/AlgaLib"),
        default_tag=None,
    )
    await project.init_repo()

    print(await project.get_first_commit())

    # print(await project.get_git_tags())

    # print(project.get_readme())
    # print(await project.extract_quark_info())
    # classes = project.get_classes()
    # # print("Found classes", [x.name for x in project.get_classes()])
    # docs = await project.build_docs()
    print("foo")


if __name__ == "__main__":
    asyncio.run(foo())
