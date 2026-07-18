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
    """Parse ``"1.21.11"`` → ``(1, 21, 11)`` (a missing patch defaults to 0).

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

#: First *pack format* that describes itself with ``min_format``/``max_format``
#: instead of the legacy ``pack_format`` field (Mojang snapshot 25w31a).  Below
#: this, ``pack_format`` is required; at or above it, it must be absent.
FORMAT_RANGE_SINCE: int = 82


@dataclass(frozen=True, slots=True)
class VersionInfo:
    """Everything the compiler resolves from a Minecraft version string."""

    version: str
    version_tuple: VersionTuple
    #: Major pack format (the ``94`` of ``94.1``).
    pack_format: int
    #: Minor pack format (the ``1`` of ``94.1``) — 0 before 1.21.9, when Mojang
    #: started bumping a minor for non-breaking data changes.
    pack_format_minor: int
    #: Inclusive ``(min, max)`` major pack-format band written to ``pack.mcmeta``.
    supported_formats: tuple[int, int]

    @property
    def singular_folders(self) -> bool:
        """True on 1.21+, where ``functions`` became ``function`` etc."""
        return self.version_tuple >= SINGULAR_FOLDERS_SINCE

    @property
    def uses_components(self) -> bool:
        """True on 1.20.5+, where item/block data uses components not NBT."""
        return self.version_tuple >= COMPONENTS_SINCE

    @property
    def uses_format_range(self) -> bool:
        """True when ``pack.mcmeta`` uses ``min_format``/``max_format``.

        At or above :data:`FORMAT_RANGE_SINCE` the legacy ``pack_format`` field
        must be *absent*, so this picks the document shape — it is not merely a
        preference.
        """
        return self.pack_format >= FORMAT_RANGE_SINCE

    @property
    def format_label(self) -> str:
        """The format as people write it: ``"94.1"`` on 1.21.9+, else ``"48"``."""
        if self.uses_format_range:
            return f"{self.pack_format}.{self.pack_format_minor}"
        return str(self.pack_format)


# --- the support table -------------------------------------------------------
# version -> (major, minor, supported_formats band). Ordered oldest to newest.
# Sources: the datapack `pack_format` history (Mojang wiki / version.json).
_ROWS: dict[str, tuple[int, int, tuple[int, int]]] = {
    "1.20.1": (15, 0, (15, 15)),
    "1.20.2": (18, 0, (18, 18)),
    "1.20.4": (26, 0, (26, 26)),
    "1.20.5": (41, 0, (41, 41)),
    "1.20.6": (41, 0, (41, 41)),
    "1.21": (48, 0, (48, 48)),
    "1.21.1": (48, 0, (48, 48)),
    "1.21.3": (57, 0, (57, 57)),
    "1.21.4": (61, 0, (61, 61)),
    "1.21.5": (71, 0, (71, 71)),
    # 1.21.9+ carry a minor format and use min_format/max_format.
    "1.21.9": (88, 0, (88, 88)),
    "1.21.10": (88, 0, (88, 88)),
    "1.21.11": (94, 1, (94, 94)),
}

SUPPORT_TABLE: dict[str, VersionInfo] = {
    version: VersionInfo(version, parse_version(version), major, minor, band)
    for version, (major, minor, band) in _ROWS.items()
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
