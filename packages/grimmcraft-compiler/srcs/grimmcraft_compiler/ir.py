"""The dialect-independent intermediate representation (IR).

The IR is a plain description of a datapack: a set of :class:`Function`\\ s (a
namespaced id plus an ordered list of declarative commands), the function
:class:`FunctionTag`\\ s (``minecraft:load`` / ``minecraft:tick`` and any custom
ones), and a bag of JSON :class:`Resource`\\ s (loot tables, recipes, …).  It
knows nothing about command *text* — that is the :class:`~.dialect.Dialect`'s job
— so the same IR can be rendered for any target version.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from grimmcraft_control.machine import Command

#: Allowed characters in a resource-location namespace / path segment.
_NAMESPACE_RE = re.compile(r"^[a-z0-9_.-]+$")
_PATH_RE = re.compile(r"^[a-z0-9_./-]+$")


@dataclass(frozen=True, slots=True)
class ResourceLocation:
    """A ``namespace:path`` id, e.g. ``grimmcraft:door/on_open``.

    :meth:`invalid_reason` reports *why* a location is malformed (used by the
    validator to raise a helpful diagnostic); construction itself never raises so
    the validator can inspect bad input rather than crash.
    """

    namespace: str
    path: str

    @classmethod
    def parse(cls, raw: str, *, default_namespace: str = "minecraft") -> ResourceLocation:
        """Parse ``"ns:path"`` (or a bare ``"path"``, which takes the default ns)."""
        if ":" in raw:
            namespace, path = raw.split(":", 1)
        else:
            namespace, path = default_namespace, raw
        return cls(namespace, path)

    def invalid_reason(self) -> str | None:
        """A human explanation if this location is malformed, else ``None``."""
        if not _NAMESPACE_RE.match(self.namespace):
            return (
                f"namespace {self.namespace!r} has invalid characters; allowed: "
                "[a-z0-9_.-]"
            )
        if not _PATH_RE.match(self.path):
            return f"path {self.path!r} has invalid characters; allowed: [a-z0-9_./-]"
        return None

    def __str__(self) -> str:
        return f"{self.namespace}:{self.path}"


@dataclass(slots=True)
class Function:
    """A named ``mcfunction``: an ordered list of declarative commands."""

    id: ResourceLocation
    commands: list[Command] = field(default_factory=list)
    comment: str | None = None

    def add(self, command: Command) -> None:
        self.commands.append(command)


@dataclass(slots=True)
class FunctionTag:
    """A ``tags/function`` list — e.g. ``minecraft:load`` / ``minecraft:tick``."""

    id: ResourceLocation
    values: list[ResourceLocation] = field(default_factory=list)


@dataclass(slots=True)
class Resource:
    """An arbitrary JSON resource (loot table, recipe, predicate, …).

    ``category`` is the datapack sub-folder base name in *singular* form
    (``loot_table``, ``recipe``, …); the emitter pluralises it for older
    versions.  ``content`` is any JSON-serialisable object.
    """

    id: ResourceLocation
    category: str
    content: dict[str, Any]


@dataclass(slots=True)
class Datapack:
    """The whole IR: pack metadata plus functions, tags and resources."""

    namespace: str
    description: str
    functions: list[Function] = field(default_factory=list)
    tags: list[FunctionTag] = field(default_factory=list)
    resources: list[Resource] = field(default_factory=list)

    def add_function(self, function: Function) -> Function:
        self.functions.append(function)
        return function

    def function_ids(self) -> set[str]:
        """Every function id in the pack, as ``ns:path`` strings."""
        return {str(f.id) for f in self.functions}
