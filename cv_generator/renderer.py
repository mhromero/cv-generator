"""Render structured CV data as moderncv LaTeX."""

from __future__ import annotations

from .model import CV, Entry, Project


# moderncv 2.4+ uses separate first/last-name and section-style commands.
# Keep the supplied intermediate template unchanged, and apply these overrides
# only to the temporary source used for PDF compilation.
MODERNCV_COMPATIBILITY = r"""
% Compatibility overrides for moderncv versions with separate name styles.
\renewcommand*{\namefont}{\Large\sffamily\bfseries}
\renewcommand*{\firstnamestyle}[1]{{\namefont\textcolor{color1}{#1}}}
\renewcommand*{\lastnamestyle}[1]{{\namefont\textcolor{color1}{#1}}}
\renewcommand*{\namestyle}[1]{{\Large\sffamily\bfseries\textcolor{color1}{#1}}}
\renewcommand*{\titlefont}{\large\sffamily\color{black!65}}
\renewcommand*{\titlestyle}[1]{{\titlefont#1}}
\renewcommand*{\sectionfont}{\Large\sffamily\bfseries}
\renewcommand*{\sectionstyle}[1]{{\sectionfont\textcolor{color1}{#1}}}
\colorlet{sectioncolor}{color1}
\colorlet{bodyrulecolor}{color1}
\makeatletter
\@ifundefined{sectionrule}{}{%
  \renewcommand*{\sectionrule}{\par\nobreak\vspace*{-.7\baselineskip}\leavevmode{\color{color1}\leaders\hbox{\rule{1pt}{0.4pt}}\hfill\kern0pt}}}
\@ifundefined{makehead}{}{%
  \patchcmd{\makehead}{\titlestyle{~|~\@title}}{\titlestyle{~--~\@title}}{}{}}
\makeatother
"""


def _latex(value: str) -> str:
    """Escape Markdown text for a LaTeX argument and match moderncv dashes."""

    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "—": "--",
    }
    return "".join(replacements.get(character, character) for character in value)


def add_moderncv_compatibility(tex: str) -> str:
    """Add current-moderncv visual fixes to the temporary compile source."""

    marker = "\\begin{document}\n"
    if marker not in tex:
        raise ValueError("Generated LaTeX is missing the document start marker")
    return tex.replace(marker, MODERNCV_COMPATIBILITY + marker, 1)


def _name_parts(name: str) -> tuple[str, str]:
    """Split a full name into the two arguments required by moderncv."""

    first, separator, last = name.partition(" ")
    if not separator:
        return name, ""
    return first, last


def _render_bullets(bullets: list[str]) -> list[str]:
    """Render a list of CV bullets."""

    return ["\\begin{itemize}", *[f"\\item {_latex(item)}" for item in bullets], "\\end{itemize}"]


def _render_entry(entry: Entry, command: str) -> list[str]:
    """Render an experience or education entry."""

    prefix = (
        f"\\{command}{{{_latex(entry.dates)}}}{{{_latex(entry.title)}}}"
        f"{{{_latex(entry.organization)}}}{{{_latex(entry.location)}}}{{}}"
    )
    if entry.bullets:
        body = _render_bullets(entry.bullets)
        body[-1] += "}"
        return [prefix + "{", *body]
    return [prefix + "{" + _latex(entry.description) + "}"]


def _render_project(project: Project) -> list[str]:
    """Render a project with either bullets or an inline description."""

    title = _latex(project.title)
    dates = _latex(project.dates)
    tech = _latex(project.technologies)
    lines = [f"\\cvprojectentry{{{title}}}{{{dates}}}{{"]
    if tech:
        if project.description:
            lines.append(f"\\textit{{{tech}}} -- {_latex(project.description)}")
        else:
            lines.append(f"\\textit{{{tech}}}")
    if project.bullets:
        lines.extend(_render_bullets(project.bullets))
        lines[-1] += "}"
    elif lines[-1] != f"\\cvprojectentry{{{title}}}{{{dates}}}{{":
        lines[-1] += "}"
    else:
        lines.append("}")
    return lines


def render_moderncv(cv: CV) -> str:
    """Render a CV using the moderncv banking/purple template."""

    first_name, last_name = _name_parts(cv.name)
    contact = cv.contact
    links: list[str] = []
    if contact.linkedin:
        links.append(
            f"\\href{{{contact.linkedin}}}{{{_latex(contact.linkedin.removeprefix('https://'))}}}"
        )
    if contact.github:
        links.append(
            f"\\href{{{contact.github}}}{{{_latex(contact.github.removeprefix('https://'))}}}"
        )
    extra = r" \quad $\vert$ \quad ".join(links)

    lines = [
        r"\documentclass[10pt,a4paper,sans]{moderncv}",
        "",
        r"\moderncvstyle[nosymbols]{banking}",
        r"\moderncvcolor{purple}",
        "",
        r"\usepackage[scale=0.82,top=0.6cm,bottom=0.6cm]{geometry}",
        r"\usepackage[utf8]{inputenc}",
        r"\renewcommand*{\bfdefault}{bx}",
        "",
        f"\\name{{{_latex(first_name)}}}{{{_latex(last_name)}}}",
        f"\\title{{{_latex(cv.title)}}}",
        f"\\phone[mobile]{{{_latex(contact.phone)}}}",
        f"\\email{{{_latex(contact.email)}}}",
        f"\\extrainfo{{{extra}}}",
        f"\\address{{{_latex(contact.location)}}}{{}}{{}}",
        "",
        r"\renewcommand*{\namestyle}[1]{{\Large\sffamily\bfseries\textcolor{color1}{#1}}}",
        r"\renewcommand*{\titlefont}{\large\sffamily\color{black!65}}",
        r"\newcommand*{\cvprojectentry}[3]{%",
        r"  \begin{tabular*}{\maincolumnwidth}{l@{\extracolsep{\fill}}r}",
        r"    \textbf{#1} & \textbf{#2}\\",
        r"  \end{tabular*}\\",
        r"  #3\par\addvspace{.25em}}",
        "",
        r"\begin{document}",
        r"\makecvtitle",
        "",
        r"\section{Profile}",
        f"\\cvitem{{}}{{{_latex(cv.profile)}}}",
        "",
        r"\section{Experience}",
    ]

    for index, entry in enumerate(cv.experience):
        lines.extend(_render_entry(entry, "cventry"))
        if index != len(cv.experience) - 1:
            lines.append("")

    lines.extend(["", r"\section{Projects}"])
    for index, project in enumerate(cv.projects):
        lines.extend(_render_project(project))
        if index != len(cv.projects) - 1:
            lines.append("")

    lines.extend(["", r"\section{Education}"])
    for index, entry in enumerate(cv.education):
        lines.extend(_render_entry(entry, "cventry"))
        if index != len(cv.education) - 1:
            lines.append("")

    lines.extend(["", r"\section{Technical Skills}"])
    lines.extend(
        f"\\cvitem{{\\color{{color1}}{_latex(category)}}}{{{_latex(value)}}}"
        for category, value in cv.skills
    )

    lines.extend(["", r"\section{Awards}"])
    lines.extend(f"\\cvitem{{}}{{{_latex(award)}}}" for award in cv.awards)
    lines.extend(["", r"\end{document}"])
    return "\n".join(lines) + "\n"
