"""Founder prompt loader using Jinja2."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound


class UnknownPrompt(KeyError):
    """Raised when a named prompt template does not exist."""


_PROMPT_DIR = Path(__file__).parent / "prompts"
_ENV = Environment(
    loader=FileSystemLoader(_PROMPT_DIR),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)


def list_prompts() -> list[str]:
    """Return sorted names of all installed Jinja2 prompt templates."""
    return sorted(p.stem for p in _PROMPT_DIR.glob("*.jinja2"))


def render_prompt(name: str, **vars: object) -> str:
    """Render the named prompt template with ``vars`` substituted.

    Raises ``UnknownPrompt`` if no template named ``<name>.jinja2`` exists.
    """
    try:
        template = _ENV.get_template(f"{name}.jinja2")
    except TemplateNotFound as exc:
        raise UnknownPrompt(name) from exc
    return template.render(**vars)
