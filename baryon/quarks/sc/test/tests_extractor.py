import shutil
from pathlib import Path

from django.test import TestCase

from ..extractor import *
from ..scraper import *


class ExtractorTestCase(TestCase):
    def setUp(self) -> None:
        self.raw_doc_html_path = Path(__file__).parent.joinpath(
            "assets/Fb1_ODE_raw.html"
        )

    def get_project_repo(self) -> ProjectRepo:
        return ProjectRepo(
            project_type=ProjectType.QUARK,
            name="miSCellaneous_lib",
            url="https://github.com/dkmayer/miSCellaneous_lib",
            repo_path=Path(
                "/Users/scheiba/github/sc-quarks/baryon/repos/miSCellaneous_lib"
            ),
            default_tag=None,
        )

    def test_raw_doc_file_exists(self):
        self.assertTrue(self.raw_doc_html_path.is_file())

    def test_fix_doc_links(self):
        # hack b/c lxml needs the file in read mode
        # not a good test but better than nothing
        project = self.get_project_repo()
        html_target = self.raw_doc_html_path.parent.joinpath("Fb1_ODE.html")
        shutil.copy(self.raw_doc_html_path, html_target)
        try:
            with open(html_target, "w") as f:
                with self.raw_doc_html_path.open("r") as f_source:
                    text = f_source.read()
                    f.write(text)
            self.assertFalse("https://github.com/dkmayer/miSCellaneous_lib" in text)

            project.fix_doc_links(
                help_files=[
                    HelpFile(
                        source_path=Path(
                            "/Users/scheiba/github/sc-quarks/baryon/repos/miSCellaneous_lib/HelpSource/Classes/Fb1_ODE.schelp"
                        ),
                        html_path=html_target,
                    )
                ],
            )
            with open(html_target, "r", encoding="utf-8") as f:
                text = f.read()

            # check if link to self was redirected properly
            self.assertTrue('<a href="./Fb1_ODE.html">Fb1_ODE</a>' in text)

            # docs should be linked properly - this is linked to main b/c there was no check for main prior so this
            # test resource is offline
            self.assertTrue(
                "https://github.com/dkmayer/miSCellaneous_lib/blob/main/HelpSource/Classes/Fb1_ODE.schelp"
                in text
            )

        finally:
            os.remove(html_target)

    def test_get_relative_path_str(self):
        self.assertEqual(
            "./bar.html",
            ProjectRepo._get_relative_path_str(
                path=Path("/hello/world/bar.html"),
                relative_to=Path("/hello/world"),
            ),
        )

        self.assertEqual(
            "../bar.html",
            ProjectRepo._get_relative_path_str(
                path=Path("/hello/bar.html"),
                relative_to=Path("/hello/world"),
            ),
        )

        self.assertEqual(
            "../new/bar.html",
            ProjectRepo._get_relative_path_str(
                path=Path("/hello/new/bar.html"),
                relative_to=Path("/hello/world"),
            ),
        )

        with self.assertRaises(Exception):
            ProjectRepo._get_relative_path_str(
                path=Path("/no/thing/in/common.html"),
                relative_to=Path(
                    "/too/far/apart/will/not/work/because/of/max/recursion"
                ),
            )
