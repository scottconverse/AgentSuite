"""Design brief-template loader."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound


class UnknownTemplate(KeyError):
    """Raised when a named brief template does not exist."""


_TEMPLATE_DIR = Path(__file__).parent / "templates"
_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    variable_start_string="{{",
    variable_end_string="}}",
)

TEMPLATE_NAMES = [
    "banner-ad",
    "email-header",
    "social-graphic",
    "landing-hero",
    "deck-slide",
    "print-flyer",
    "video-thumbnail",
    "icon-set",
]


def list_templates() -> list[str]:
    """Return sorted names of all installed brief templates."""
    return sorted(p.stem for p in _TEMPLATE_DIR.glob("*.md"))


def render_template(name: str, **vars: object) -> str:
    """Render the named brief template with ``vars`` substituted.

    Raises ``UnknownTemplate`` if no template named ``<name>.md`` exists.
    """
    try:
        template = _ENV.get_template(f"{name}.md")
    except TemplateNotFound as exc:
        raise UnknownTemplate(name) from exc
    return template.render(**vars)
