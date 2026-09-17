"""Command-line interface for generating CV LaTeX and PDFs."""

from __future__ import annotations

import argparse
import difflib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .parser import CVParseError, parse_file
from .renderer import add_moderncv_compatibility, render_moderncv


def _build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(description="Generate a PDF CV from Markdown.")
    parser.add_argument("input", type=Path, help="Markdown CV definition")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output PDF path (defaults to the input path with a .pdf suffix)",
    )
    parser.add_argument(
        "--tex-output",
        type=Path,
        help="Also save the generated intermediate LaTeX to this path",
    )
    parser.add_argument(
        "--compare-to",
        type=Path,
        help="Compare generated LaTeX with this reference file and fail on differences",
    )
    parser.add_argument(
        "--template",
        choices=("moderncv",),
        default="moderncv",
        help="LaTeX template to use (default: moderncv)",
    )
    parser.add_argument(
        "--latex-engine",
        default="pdflatex",
        help="LaTeX executable (default: pdflatex)",
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Generate and validate LaTeX without compiling a PDF",
    )
    return parser


def _write_text(path: Path, content: str) -> None:
    """Create parent directories and write UTF-8 text."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _compare(reference: Path, generated: str) -> None:
    """Raise an error containing a compact unified diff when files differ."""

    expected = reference.read_text(encoding="utf-8")
    if expected == generated:
        print(f"LaTeX matches reference: {reference}")
        return
    diff = "".join(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            generated.splitlines(keepends=True),
            fromfile=str(reference),
            tofile="generated",
        )
    )
    raise ValueError(f"Generated LaTeX differs from {reference}:\n{diff}")


def _compile_pdf(tex: str, output: Path, engine: str, stem: str) -> None:
    """Compile LaTeX in a temporary directory and copy the resulting PDF out."""

    executable = shutil.which(engine)
    if executable is None:
        raise RuntimeError(
            f"Could not find {engine!r}. Install a LaTeX distribution, then run the command again."
        )
    with tempfile.TemporaryDirectory(prefix="cv-generator-") as temp_dir:
        temp = Path(temp_dir)
        tex_path = temp / f"{stem}.tex"
        tex_path.write_text(tex, encoding="utf-8")
        command = [
            executable,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory",
            str(temp),
            str(tex_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            output_text = (result.stdout + "\n" + result.stderr).strip()
            raise RuntimeError(f"LaTeX compilation failed:\n{output_text}")
        compiled = temp / f"{stem}.pdf"
        if not compiled.exists():
            raise RuntimeError("LaTeX reported success but did not create a PDF")
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(compiled, output)


def main(argv: list[str] | None = None) -> int:
    """Run the CV generator and return a shell-friendly exit status."""

    args = _build_parser().parse_args(argv)
    try:
        cv = parse_file(args.input)
        if args.template != "moderncv":  # Defensive guard for future templates.
            raise ValueError(f"Unsupported template: {args.template}")
        tex = render_moderncv(cv)
        if args.tex_output:
            _write_text(args.tex_output, tex)
            print(f"Wrote LaTeX: {args.tex_output}")
        if args.compare_to:
            _compare(args.compare_to, tex)
        if args.no_pdf:
            return 0
        output = args.output or args.input.with_suffix(".pdf")
        _compile_pdf(add_moderncv_compatibility(tex), output, args.latex_engine, args.input.stem)
        print(f"Wrote PDF: {output}")
        return 0
    except (CVParseError, OSError, RuntimeError, ValueError) as error:
        print(f"cvgen: error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover - exercised through the console script.
    raise SystemExit(main())
