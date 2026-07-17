"""The :class:`Target` — the version + flavor that drives the whole compile."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from grimmcraft_compiler.version import VersionInfo, resolve_version


class Flavor(Enum):
    """The server/loader flavor a datapack targets.

    * ``VANILLA`` — strict vanilla command set.
    * ``PAPER`` — vanilla datapack semantics; documented Paper additions allowed.
    * ``FABRIC`` — vanilla-compatible datapack; commands needing a Fabric mod API
      are warned about rather than silently emitted.
    """

    VANILLA = "vanilla"
    PAPER = "paper"
    FABRIC = "fabric"

    @classmethod
    def parse(cls, value: str) -> Flavor:
        """Parse a case-insensitive flavor name, or raise ``ValueError``."""
        try:
            return cls(value.lower())
        except ValueError:
            names = ", ".join(f.value for f in cls)
            raise ValueError(
                f"unknown flavor {value!r}; choose one of: {names}"
            ) from None


@dataclass(frozen=True, slots=True)
class Target:
    """The compile target: which Minecraft ``version`` and which ``flavor``.

    Construct via :meth:`resolve` so the version is validated against the support
    table up front (fail fast).  :attr:`info` exposes the resolved
    ``pack_format``, folder scheme and component/NBT choice.
    """

    version: str
    flavor: Flavor
    info: VersionInfo

    @classmethod
    def resolve(cls, version: str, flavor: Flavor | str) -> Target:
        """Build a fully-resolved target, validating the version + flavor combo.

        Raises :class:`ValueError` for an unsupported version or flavor.
        """
        flavor_enum = flavor if isinstance(flavor, Flavor) else Flavor.parse(flavor)
        info = resolve_version(version)
        return cls(version=version, flavor=flavor_enum, info=info)

    def __str__(self) -> str:
        return f"{self.version} {self.flavor.value}"
