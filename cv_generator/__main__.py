"""Allow ``python -m cv_generator`` to invoke the CLI."""

from .cli import main


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI.
    raise SystemExit(main())
