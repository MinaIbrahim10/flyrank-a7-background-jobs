"""In-memory report storage shared by the API and background functions."""

from typing import Any


reports: dict[str, dict[str, Any]] = {}

