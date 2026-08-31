from threading import Lock
from typing import Any

reports: dict[str, dict[str, Any]] = {}
reports_lock = Lock()
