"""Detect the :class:`Target` a datapack was built for — the inverse of the
compiler's version table.

Three signals, strongest first:

1. **The description hint.**  ``compile_machines`` writes a description ending in
   ``"… for <version> <flavor>"``.  When present it pins both exactly, which is
   what makes a byte-identical round-trip possible (a bare ``pack_format`` cannot
   distinguish 1.21 from 1.21.1 — they share format 48).
2. **The pack format.**  ``pack_format`` (legacy) or ``min_format``/``max_format``
   (1.21.9+) narrows the candidates via the compiler's ``SUPPORT_TABLE``.
3. **The folder scheme.**  Singular ``function/`` means 1.21+, plural
   ``functions/`` means older — used to narrow further, and to *contradict* the
   format when a pack is inconsistent (``GD2001``).

Detection never guesses silently: an ambiguous or contradictory result is
reported through the diagnostic bag and recorded in :attr:`Detection.confidence`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from grimmcraft_compiler.target import Flavor, Target
from grimmcraft_compiler.version import SUPPORT_TABLE, VersionInfo, supported_versions
from grimmcraft_decompiler.diagnostics import Codes, DiagnosticBag
from grimmcraft_decompiler.source import PACK_META, PackSource

#: Matches the tail the compiler writes into a pack description, e.g.
#: ``"tutorial — grimmcraft datapack for 1.21.1 vanilla"``.
_DESCRIPTION_HINT = re.compile(
    r"for\s+(?P<version>\d+\.\d+(?:\.\d+)?)\s+(?P<flavor>vanilla|paper|fabric)\s*$"
)


class Confidence(Enum):
    """How firmly the target was pinned down."""

    #: The description named the exact version and flavor.
    EXACT = "exact"
    #: The pack format (and folder scheme) matched exactly one supported version.
    HIGH = "high"
    #: Several versions share this pack format; the newest matching one was used.
    AMBIGUOUS = "ambiguous"
    #: Nothing matched; the caller-supplied or default target was used.
    FALLBACK = "fallback"


@dataclass(frozen=True, slots=True)
class Detection:
    """The detected target plus the evidence behind it."""

    target: Target
    confidence: Confidence
    #: Every supported version consistent with the evidence, oldest first.
    candidates: tuple[str, ...]
    #: The raw ``pack.mcmeta`` document, or ``None`` when it was missing/invalid.
    mcmeta: dict[str, Any] | None
    #: The pack description, needed verbatim to re-emit an identical pack.
    description: str
    #: True when the tree uses singular (1.21+) resource folders.
    singular_folders: bool

    @property
    def info(self) -> VersionInfo:
        return self.target.info


def _parse_mcmeta(source: PackSource, bag: DiagnosticBag) -> dict[str, Any] | None:
    """Read and parse ``pack.mcmeta``, reporting ``GD1002`` if it is unusable."""
    raw = source.read(PACK_META)
    if raw is None:
        bag.emit(
            Codes.MISSING_PACK_MCMETA,
            f"'{PACK_META}' not found at the pack root",
            hint="point at the datapack folder itself (the one containing pack.mcmeta)",
            source=source.label,
        )
        return None
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        bag.emit(
            Codes.MISSING_PACK_MCMETA,
            f"'{PACK_META}' is not valid JSON: {exc.msg}",
            hint="fix the JSON syntax, or decompile the folder this pack came from",
            source=f"{PACK_META}:{exc.lineno}",
        )
        return None
    if not isinstance(document, dict) or not isinstance(document.get("pack"), dict):
        bag.emit(
            Codes.MISSING_PACK_MCMETA,
            f"'{PACK_META}' has no 'pack' object",
            hint='expected {"pack": {"pack_format": …, "description": …}}',
            source=PACK_META,
        )
        return None
    return document


def _major_format(document: dict[str, Any]) -> int | None:
    """The major pack format, from either the legacy or the modern field set.

    Legacy packs carry ``pack_format``; 1.21.9+ packs carry ``min_format``, which
    is either a bare major or a ``[major, minor]`` pair.
    """
    pack = document["pack"]
    value = pack.get("pack_format")
    if isinstance(value, int):
        return value
    value = pack.get("min_format")
    if isinstance(value, int):
        return value
    if isinstance(value, list) and value and isinstance(value[0], int):
        return int(value[0])
    return None


def _uses_singular_folders(source: PackSource) -> bool:
    """Whether the tree stores functions in singular ``function/`` folders.

    Reads the actual directory names rather than trusting the format, so a
    mismatch between the two can be diagnosed.
    """
    for path in source.files:
        parts = path.split("/")
        if len(parts) > 2 and parts[0] == "data":
            # data/<ns>/function/… or data/<ns>/tags/function/…
            for segment in parts[2:]:
                if segment == "function":
                    return True
                if segment == "functions":
                    return False
    return True


def _candidates_for_format(major: int) -> list[str]:
    """Every supported version whose major pack format is ``major``, oldest first."""
    return [v for v, info in SUPPORT_TABLE.items() if info.pack_format == major]


def detect_target(
    source: PackSource,
    bag: DiagnosticBag,
    *,
    override: str | None = None,
    flavor: Flavor | str = Flavor.VANILLA,
) -> Detection:
    """Resolve the :class:`Target` for ``source``, appending diagnostics to ``bag``.

    ``override`` forces a version (the CLI's ``--version``), skipping inference
    but still reading the description so the pack can be re-emitted verbatim.
    """
    document = _parse_mcmeta(source, bag)
    pack = document["pack"] if document else {}
    description = pack.get("description", "")
    if not isinstance(description, str):
        description = str(description)
    singular = _uses_singular_folders(source)

    hint = _DESCRIPTION_HINT.search(description)
    hinted_version = hint.group("version") if hint else None
    hinted_flavor = hint.group("flavor") if hint else None
    resolved_flavor = Flavor.parse(hinted_flavor) if hinted_flavor else Flavor.parse(
        flavor.value if isinstance(flavor, Flavor) else flavor
    )

    major = _major_format(document) if document else None
    candidates = _candidates_for_format(major) if major is not None else []

    # An explicit override wins outright.
    if override is not None:
        return Detection(
            target=Target.resolve(override, resolved_flavor),
            confidence=Confidence.EXACT,
            candidates=tuple(candidates),
            mcmeta=document,
            description=description,
            singular_folders=singular,
        )

    # Signal 1: the description names the version outright.
    if hinted_version is not None and hinted_version in SUPPORT_TABLE:
        target = Target.resolve(hinted_version, resolved_flavor)
        _warn_scheme_mismatch(target.info, singular, bag, source)
        return Detection(
            target=target,
            confidence=Confidence.EXACT,
            candidates=tuple(candidates or [hinted_version]),
            mcmeta=document,
            description=description,
            singular_folders=singular,
        )

    # Signal 2 + 3: pack format, narrowed by the folder scheme.
    if major is None:
        bag.emit(
            Codes.UNKNOWN_PACK_FORMAT,
            "could not read a pack format from pack.mcmeta "
            "(no 'pack_format' or 'min_format')",
            hint=f"pass --version explicitly; supported: {', '.join(supported_versions())}",
            source=PACK_META,
        )
        return _fallback(document, description, singular, resolved_flavor)

    if not candidates:
        bag.emit(
            Codes.UNKNOWN_PACK_FORMAT,
            f"pack format {major} does not map to any supported Minecraft version",
            hint=(
                "pass --version to decompile anyway; supported versions are: "
                + ", ".join(supported_versions())
            ),
            source=PACK_META,
        )
        return _fallback(document, description, singular, resolved_flavor)

    narrowed = [v for v in candidates if SUPPORT_TABLE[v].singular_folders is singular]
    if not narrowed:
        scheme = "singular 'function/'" if singular else "plural 'functions/'"
        expected = "plural 'functions/'" if singular else "singular 'function/'"
        bag.emit(
            Codes.FOLDER_SCHEME_MISMATCH,
            f"the tree uses {scheme} folders, but pack format {major} "
            f"({', '.join(candidates)}) expects {expected}. Minecraft renamed the "
            "datapack resource folders to their singular form in 1.21",
            hint="pass --version to pick a side; the folder scheme is what the game reads",
            source=PACK_META,
        )
        narrowed = candidates

    chosen = narrowed[-1]  # newest matching version
    confidence = Confidence.HIGH if len(narrowed) == 1 else Confidence.AMBIGUOUS
    if confidence is Confidence.AMBIGUOUS:
        bag.emit(
            Codes.AMBIGUOUS_VERSION,
            f"pack format {major} is shared by {', '.join(narrowed)}; "
            f"assuming {chosen}",
            hint=f"pass --version to pin one (e.g. --version {narrowed[0]})",
            source=PACK_META,
        )

    return Detection(
        target=Target.resolve(chosen, resolved_flavor),
        confidence=confidence,
        candidates=tuple(narrowed),
        mcmeta=document,
        description=description,
        singular_folders=singular,
    )


def _warn_scheme_mismatch(
    info: VersionInfo, singular: bool, bag: DiagnosticBag, source: PackSource
) -> None:
    """Report ``GD2001`` when the on-disk folders contradict the chosen version."""
    if info.singular_folders is singular:
        return
    actual = "singular 'function/'" if singular else "plural 'functions/'"
    expected = "singular 'function/'" if info.singular_folders else "plural 'functions/'"
    bag.emit(
        Codes.FOLDER_SCHEME_MISMATCH,
        f"the tree uses {actual} folders, but {info.version} expects {expected} "
        "(the folders were renamed to their singular form in 1.21)",
        hint="re-emitting will use the version's scheme, which changes the layout",
        source=source.label,
    )


def _fallback(
    document: dict[str, Any] | None,
    description: str,
    singular: bool,
    flavor: Flavor,
) -> Detection:
    """The newest supported version matching the folder scheme, as a last resort."""
    matching = [v for v, i in SUPPORT_TABLE.items() if i.singular_folders is singular]
    chosen = (matching or supported_versions())[-1]
    return Detection(
        target=Target.resolve(chosen, flavor),
        confidence=Confidence.FALLBACK,
        candidates=tuple(matching),
        mcmeta=document,
        description=description,
        singular_folders=singular,
    )
