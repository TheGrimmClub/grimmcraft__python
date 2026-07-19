"""Reading and writing the command inventory, in either supported format.

An inventory is either a plain text file (one command per line) or a JSON file of
objects carrying ``command`` plus the source ``dimension``/``x``/``y``/``z`` the
command block sat at.  The format is detected from the content, and writing
preserves whichever came in — so coordinates survive a round trip and a migrated
command can still be traced back to the block it came from.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CommandEntry:
    """One command, with wherever it was found."""

    command: str
    dimension: str | None = None
    x: int | None = None
    y: int | None = None
    z: int | None = None
    #: Anything else the inventory carried, preserved on write.
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def has_position(self) -> bool:
        return None not in (self.x, self.y, self.z)

    @property
    def location(self) -> str:
        """A short human label, used in reports and generated file names."""
        if not self.has_position:
            return "unknown"
        dimension = (self.dimension or "overworld").split(":")[-1]
        return f"{dimension}_{self.x}_{self.y}_{self.z}"

    def to_json(self) -> dict[str, Any]:
        document: dict[str, Any] = {**self.extra, "command": self.command}
        if self.dimension is not None:
            document["dimension"] = self.dimension
        for axis, value in (("x", self.x), ("y", self.y), ("z", self.z)):
            if value is not None:
                document[axis] = value
        return document


@dataclass
class Inventory:
    """A whole inventory, remembering which format it was read from."""

    entries: list[CommandEntry] = field(default_factory=list)
    #: ``"json"`` or ``"text"`` — what :meth:`write` will produce.
    format: str = "text"

    def __iter__(self) -> Any:
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)

    def write(self, path: str | Path) -> Path:
        """Write the inventory back out in its original format."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if self.format == "json":
            destination.write_text(
                json.dumps([entry.to_json() for entry in self.entries], indent=2)
                + "\n",
                encoding="utf-8",
            )
        else:
            destination.write_text(
                "".join(f"{entry.command}\n" for entry in self.entries),
                encoding="utf-8",
            )
        return destination


def _entry_from_json(document: Any) -> CommandEntry | None:
    """One JSON object → a :class:`CommandEntry`, or ``None`` if it has no command."""
    if isinstance(document, str):
        return CommandEntry(command=document)
    if not isinstance(document, dict):
        return None
    command = document.get("command")
    if not isinstance(command, str):
        return None
    known = {"command", "dimension", "x", "y", "z"}
    return CommandEntry(
        command=command,
        dimension=document.get("dimension"),
        x=document.get("x"),
        y=document.get("y"),
        z=document.get("z"),
        extra={k: v for k, v in document.items() if k not in known},
    )


def read_inventory(path: str | Path) -> Inventory:
    """Read an inventory, detecting JSON or one-command-per-line text.

    Detection is by *content*, not by extension: an inventory exported by another
    tool may be called anything, and guessing from the suffix would fail loudly
    at the wrong moment.
    """
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    stripped = text.lstrip()

    if stripped.startswith(("[", "{")):
        document = json.loads(text)
        if isinstance(document, dict):
            # Tolerate a wrapper object such as {"commands": [...]}.
            for key in ("commands", "entries", "blocks"):
                if isinstance(document.get(key), list):
                    document = document[key]
                    break
        if not isinstance(document, list):
            raise ValueError(
                f"{source}: expected a JSON array of command objects, "
                f"found {type(document).__name__}"
            )
        entries = [
            entry for entry in (_entry_from_json(item) for item in document)
            if entry is not None
        ]
        return Inventory(entries=entries, format="json")

    entries = [
        CommandEntry(command=line.strip())
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return Inventory(entries=entries, format="text")
