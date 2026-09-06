"""Renderers."""

from clone_trap.output.json import render_json, report_to_dict
from clone_trap.output.text import render_text

__all__ = ["render_json", "render_text", "report_to_dict"]
