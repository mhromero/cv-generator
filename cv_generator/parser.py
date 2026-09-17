"""Parse the small, deliberately constrained Markdown CV format."""

from __future__ import annotations

import re
from pathlib import Path

from .model import CV, Contact, Entry, Project


class CVParseError(ValueError):
    """Raised when a Markdown CV does not follow the supported structure."""


_BOLD_LINE = re.compile(r"^\*\*(.+?)\*\*$")
_CONTACT_LINE = re.compile(r"^- \*\*(.+?):\*\*\s*(.*)$")
_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
_SKILL_LINE = re.compile(r"^- \*\*(.+?):\*\*\s*(.*)$")
_TECH_LINE = re.compile(r"^\*(.+?)\*(?:\s+—\s+(.*))?$")


def _content_lines(markdown: str) -> list[str]:
    """Normalize line endings and remove surrounding blank lines."""

    return markdown.replace("\r\n", "\n").replace("\r", "\n").strip().splitlines()


def _require_heading(line: str, level: int, context: str) -> str:
    """Return heading text or raise a useful error for malformed input."""

    prefix = "#" * level + " "
    if not line.startswith(prefix):
        raise CVParseError(f"Expected a level-{level} heading for {context!r}, got: {line!r}")
    return line[len(prefix) :].strip()


def _section_blocks(lines: list[str]) -> dict[str, list[str]]:
    """Split the document into level-two heading sections."""

    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        if line.startswith("## "):
            current = line[3:].strip()
            if current in sections:
                raise CVParseError(f"Duplicate section: {current}")
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
        elif line.strip():
            raise CVParseError("Content found before the first CV section")
    return sections


def _blocks(lines: list[str]) -> list[list[str]]:
    """Return non-empty blocks separated by blank lines."""

    result: list[list[str]] = []
    block: list[str] = []
    for line in lines:
        if line.strip():
            block.append(line)
        elif block:
            result.append(block)
            block = []
    if block:
        result.append(block)
    return result


def _heading_blocks(lines: list[str]) -> list[list[str]]:
    """Group each level-three heading with all content until the next heading."""

    result: list[list[str]] = []
    block: list[str] | None = None
    for line in lines:
        if line.startswith("### "):
            if block:
                result.append(block)
            block = [line]
        elif block is not None:
            block.append(line)
        elif line.strip():
            raise CVParseError(f"Content found before an entry heading: {line!r}")
    if block:
        result.append(block)
    return result


def _split_date_location(line: str, context: str) -> tuple[str, str]:
    """Read the ``**dates · location**`` metadata convention."""

    match = _BOLD_LINE.match(line.strip())
    if not match:
        raise CVParseError(f"Expected bold date metadata for {context!r}")
    value = match.group(1)
    if " · " in value:
        return tuple(value.split(" · ", 1))  # type: ignore[return-value]
    return value, ""


def _split_organization(heading: str, context: str) -> tuple[str, str]:
    """Split an entry heading written as ``Title — Organization``."""

    if " — " not in heading:
        raise CVParseError(f"Expected 'Title — Organization' for {context!r}")
    return tuple(heading.split(" — ", 1))  # type: ignore[return-value]


def _parse_entry_blocks(blocks: list[list[str]], kind: str) -> list[Entry]:
    """Parse experience or education headings and their content blocks."""

    entries: list[Entry] = []
    for block_index, raw_block in enumerate(blocks):
        block = [line.strip() for line in raw_block if line.strip()]
        if not block or not block[0].startswith("### "):
            continue
        heading = block[0][4:].strip()
        title, organization = _split_organization(heading, f"{kind} entry {block_index + 1}")
        if len(block) < 2:
            raise CVParseError(f"Missing metadata for {kind} entry {heading!r}")
        dates, location = _split_date_location(block[1], heading)
        body = block[2:]
        bullets = [line[2:].strip() for line in body if line.startswith("- ")]
        prose = [line.strip() for line in body if not line.startswith("- ")]
        if bullets and prose:
            raise CVParseError(f"Mixed prose and bullets in {kind} entry {heading!r}")
        entries.append(
            Entry(
                title=title,
                organization=organization,
                dates=dates,
                location=location,
                description=" ".join(prose),
                bullets=bullets,
            )
        )
    return entries


def _parse_projects(blocks: list[list[str]]) -> list[Project]:
    """Parse project blocks with optional date and technology lines."""

    projects: list[Project] = []
    for block_index, raw_block in enumerate(blocks):
        block = [line.strip() for line in raw_block if line.strip()]
        if not block or not block[0].startswith("### "):
            continue
        title = block[0][4:].strip()
        cursor = 1
        dates = ""
        if cursor < len(block) and _BOLD_LINE.match(block[cursor].strip()):
            dates = _BOLD_LINE.match(block[cursor].strip()).group(1)  # type: ignore[union-attr]
            cursor += 1
        technologies = ""
        description = ""
        if cursor < len(block):
            match = _TECH_LINE.match(block[cursor].strip())
            if match:
                technologies = match.group(1)
                description = match.group(2) or ""
                cursor += 1
        body = block[cursor:]
        bullets = [line[2:].strip() for line in body if line.startswith("- ")]
        prose = [line.strip() for line in body if not line.startswith("- ")]
        if bullets and prose:
            raise CVParseError(f"Mixed prose and bullets in project {title!r}")
        if prose:
            description = " ".join(filter(None, [description, *prose]))
        if not technologies and not description and not bullets:
            raise CVParseError(f"Project {title!r} has no content")
        projects.append(
            Project(
                title=title,
                dates=dates,
                technologies=technologies,
                description=description,
                bullets=bullets,
            )
        )
    if not projects:
        raise CVParseError("The Projects section must contain at least one project")
    return projects


def _parse_contact(lines: list[str]) -> Contact:
    """Extract contact labels and Markdown links from the header."""

    values: dict[str, str] = {}
    for line in lines:
        match = _CONTACT_LINE.match(line.strip())
        if not match:
            raise CVParseError(f"Invalid contact line: {line!r}")
        label, value = match.groups()
        values[label.lower()] = value.strip()

    def link_value(label: str) -> str:
        value = values.get(label, "")
        match = _LINK.search(value)
        return match.group(1) if match else value

    return Contact(
        location=values.get("location", ""),
        phone=values.get("phone", ""),
        email=values.get("email", ""),
        linkedin=link_value("linkedin"),
        github=link_value("github"),
    )


def parse_markdown(markdown: str) -> CV:
    """Parse a Markdown CV into a structured :class:`CV` object."""

    lines = _content_lines(markdown)
    if len(lines) < 2:
        raise CVParseError("A CV needs a name and title")
    name = _require_heading(lines[0], 1, "name")
    title_index = next((i for i in range(1, len(lines)) if lines[i].strip()), None)
    if title_index is None:
        raise CVParseError("A CV needs a title")
    title_match = _BOLD_LINE.match(lines[title_index].strip())
    if not title_match:
        raise CVParseError("The CV title must be a bold line immediately after the name")
    title = title_match.group(1)

    first_section = next((i for i, line in enumerate(lines) if line.startswith("## ")), None)
    if first_section is None:
        raise CVParseError("The CV must contain at least one section")
    contact = _parse_contact(
        [line for line in lines[title_index + 1 : first_section] if line.strip()]
    )
    sections = _section_blocks(lines[first_section:])

    profile_blocks = _blocks(sections.get("Profile", []))
    profile = " ".join(" ".join(block).strip() for block in profile_blocks)
    if not profile:
        raise CVParseError("The Profile section cannot be empty")

    skills: list[tuple[str, str]] = []
    for line in sections.get("Technical Skills", []):
        if not line.strip():
            continue
        match = _SKILL_LINE.match(line.strip())
        if not match:
            raise CVParseError(f"Invalid technical skill line: {line!r}")
        skills.append((match.group(1), match.group(2)))

    awards = [line[2:].strip() for line in sections.get("Awards", []) if line.startswith("- ")]
    if any(line.strip() and not line.startswith("- ") for line in sections.get("Awards", [])):
        raise CVParseError("Awards must be a Markdown bullet list")

    return CV(
        name=name,
        title=title,
        contact=contact,
        profile=profile,
        experience=_parse_entry_blocks(_heading_blocks(sections.get("Experience", [])), "experience"),
        projects=_parse_projects(_heading_blocks(sections.get("Projects", []))),
        education=_parse_entry_blocks(_heading_blocks(sections.get("Education", [])), "education"),
        skills=skills,
        awards=awards,
    )


def parse_file(path: Path) -> CV:
    """Read and parse a UTF-8 Markdown CV file."""

    return parse_markdown(path.read_text(encoding="utf-8"))
