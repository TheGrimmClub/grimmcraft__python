"""Minecraft version parsing and the data-driven support table.

Everything version-specific the compiler needs — ``pack_format``, the datapack
folder scheme, whether item/block data uses *components* or *NBT* — is resolved
from :data:`SUPPORT_TABLE` here, never from scattered ``if`` statements.  Add a
new version by adding one row.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Parsed ``(major, minor, patch)`` version tuple.
VersionTuple = tuple[int, int, int]


def parse_version(version: str) -> VersionTuple:
    """Parse ``"1.21.1"`` → ``(1, 21, 1)`` (a missing patch defaults to 0).

    Raises :class:`ValueError` on anything that is not two or three dotted
    integers.
    """
    parts = version.strip().split(".")
    if not 2 <= len(parts) <= 3:
        raise ValueError(
            f"invalid Minecraft version {version!r}: expected 'MAJOR.MINOR' or "
            "'MAJOR.MINOR.PATCH'"
        )
    try:
        nums = [int(p) for p in parts]
    except ValueError as exc:
        raise ValueError(f"invalid Minecraft version {version!r}: {exc}") from None
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2])


# --- thresholds (data, not scattered conditionals) ---------------------------

#: First version whose datapacks use singular sub-folders (function, loot_table…).
SINGULAR_FOLDERS_SINCE: VersionTuple = (1, 21, 0)

#: First version where item/block data is written as components, not NBT tags.
COMPONENTS_SINCE: VersionTuple = (1, 20, 5)


@dataclass(frozen=True, slots=True)
class VersionInfo:
    """Everything the compiler resolves from a Minecraft version string."""

    version: str
    version_tuple: VersionTuple
    pack_format: int
    #: Inclusive ``(min, max)`` pack-format band written to ``pack.mcmeta``.
    supported_formats: tuple[int, int]

    @property
    def singular_folders(self) -> bool:
        """True on 1.21+, where ``functions`` became ``function`` etc."""
        return self.version_tuple >= SINGULAR_FOLDERS_SINCE

    @property
    def uses_components(self) -> bool:
        """True on 1.20.5+, where item/block data uses components not NBT."""
        return self.version_tuple >= COMPONENTS_SINCE


# --- the support table -------------------------------------------------------
# version -> (pack_format, supported_formats band). Ordered oldest to newest.
# Sources: the datapack `pack_format` history (Mojang wiki / version.json).
_ROWS: dict[str, tuple[int, tuple[int, int]]] = {
    "1.20.1": (15, (15, 15)),
    "1.20.2": (18, (18, 18)),
    "1.20.4": (26, (26, 26)),
    "1.20.5": (41, (41, 41)),
    "1.20.6": (41, (41, 41)),
    "1.21": (48, (48, 48)),
    "1.21.1": (48, (48, 48)),
    "1.21.3": (57, (57, 57)),
    "1.21.4": (61, (61, 61)),
    "1.21.5": (71, (71, 71)),
}

SUPPORT_TABLE: dict[str, VersionInfo] = {
    version: VersionInfo(version, parse_version(version), pack_format, band)
    for version, (pack_format, band) in _ROWS.items()
}


def supported_versions() -> list[str]:
    """Every version string the compiler can target, oldest first."""
    return list(SUPPORT_TABLE)


def resolve_version(version: str) -> VersionInfo:
    """Look up :class:`VersionInfo` for ``version``.

    Raises :class:`ValueError` (with the list of supported versions) if the
    version is unknown — fail fast, don't guess a ``pack_format``.
    """
    info = SUPPORT_TABLE.get(version)
    if info is None:
        known = ", ".join(supported_versions())
        raise ValueError(
            f"unsupported Minecraft version {version!r}. "
            f"Supported versions are: {known}"
        )
    return info
