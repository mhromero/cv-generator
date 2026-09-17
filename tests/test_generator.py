"""Tests for the template CV and the Markdown-to-LaTeX conversion."""

import unittest
from pathlib import Path

from cv_generator.parser import parse_file
from cv_generator.renderer import add_moderncv_compatibility, render_moderncv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class GeneratorTests(unittest.TestCase):
    """Verify the public template conversion."""

    def test_template_renders_expected_structure(self) -> None:
        """The renderer should include every supported CV section."""

        cv = parse_file(PROJECT_ROOT / "TEMPLATE.md")
        generated = render_moderncv(cv)
        self.assertIn(r"\name{[Your}{Name]}", generated)
        for section in ("Profile", "Experience", "Projects", "Education", "Technical Skills", "Awards"):
            self.assertIn(rf"\section{{{section}}}", generated)
        self.assertEqual(generated.count(r"\cvprojectentry{"), 2)

    def test_template_contains_all_sections(self) -> None:
        """The parser should retain every major CV section and entry."""

        cv = parse_file(PROJECT_ROOT / "TEMPLATE.md")
        self.assertEqual(cv.name, "[Your Name]")
        self.assertEqual(len(cv.experience), 2)
        self.assertEqual(len(cv.projects), 2)
        self.assertEqual(len(cv.education), 1)
        self.assertEqual(len(cv.skills), 4)
        self.assertEqual(len(cv.awards), 2)

    def test_compatibility_overrides_are_compile_only(self) -> None:
        """Visual compatibility fixes must not alter the supplied intermediate template."""

        cv = parse_file(PROJECT_ROOT / "TEMPLATE.md")
        generated = render_moderncv(cv)
        compiled = add_moderncv_compatibility(generated)
        self.assertIn(r"\renewcommand*{\firstnamestyle}", compiled)
        self.assertIn(r"\renewcommand*{\lastnamestyle}", compiled)
        self.assertIn(r"\renewcommand*{\sectionstyle}", compiled)
        self.assertNotEqual(generated, compiled)


if __name__ == "__main__":
    unittest.main()
