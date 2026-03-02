"""JSON Lines file audit exporter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles

if TYPE_CHECKING:
    from anonymcp.audit.events import AuditRecord


class FileExporter:
    """Appends audit records as JSON lines to a local file."""

    def __init__(self, path: str = "./audit/anonymcp.jsonl") -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    async def export(self, record: AuditRecord) -> None:
        """Append a single audit record as a JSON line."""
        line = json.dumps(record.to_dict()) + "\n"
        async with aiofiles.open(self._path, mode="a") as f:
            await f.write(line)
