"""Data structures used by the Markdown parser and LaTeX renderer."""

from dataclasses import dataclass, field


@dataclass
class Contact:
    """Contact details shown in the CV header."""

    location: str = ""
    phone: str = ""
    email: str = ""
    linkedin: str = ""
    github: str = ""


@dataclass
class Entry:
    """An experience or education entry."""

    title: str
    organization: str
    dates: str
    location: str = ""
    description: str = ""
    bullets: list[str] = field(default_factory=list)


@dataclass
class Project:
    """A project entry with optional technologies and bullet points."""

    title: str
    dates: str = ""
    technologies: str = ""
    description: str = ""
    bullets: list[str] = field(default_factory=list)


@dataclass
class CV:
    """The complete set of CV data extracted from Markdown."""

    name: str
    title: str
    contact: Contact = field(default_factory=Contact)
    profile: str = ""
    experience: list[Entry] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    education: list[Entry] = field(default_factory=list)
    skills: list[tuple[str, str]] = field(default_factory=list)
    awards: list[str] = field(default_factory=list)
