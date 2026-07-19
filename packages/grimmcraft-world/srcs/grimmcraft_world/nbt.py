"""A tiny, dependency-free reader *and writer* for Minecraft's NBT format.

NBT ("Named Binary Tag") is how Minecraft stores ``level.dat``, region chunks
and ``.nbt`` structure files. This stays dependency-free: enough to pull facts
out of ``level.dat``, and enough to write a structure file back.

Files are usually gzip-compressed; :func:`parse` auto-detects that and
:func:`dump` re-applies it by default.

**Reading is lossy about list types.** NBT distinguishes a ``TAG_List`` of ints
from a ``TAG_Int_Array``, but both arrive as a plain Python ``list``. When
writing, the type is inferred from the contents (a list of ints becomes a
``TAG_List`` of ``TAG_Int``, which is what the structure format wants). Wrap a
value in :class:`IntArray`, :class:`LongArray` or :class:`ByteArray` to force
the array form — required for chunk data, where Minecraft rejects a list.

Reference: https://minecraft.wiki/w/NBT_format
"""

from __future__ import annotations

import gzip
import struct
import zlib
from pathlib import Path
from typing import Any

from grimmclub_filesystem.checks import ContentError, expect_file

# Tag ids from the NBT spec.
TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


class _Reader:
    """A little cursor over the raw bytes, reading big-endian values."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def take(self, count: int) -> bytes:
        chunk = self.data[self.pos : self.pos + count]
        if len(chunk) != count:
            raise EOFError("Unexpected end of NBT data")
        self.pos += count
        return chunk

    def u1(self) -> int:
        return self.take(1)[0]

    def _unpack(self, fmt: str, size: int) -> Any:
        return struct.unpack(fmt, self.take(size))[0]

    def string(self) -> str:
        length = self._unpack(">H", 2)
        return self.take(length).decode("utf-8", "replace")


def _read_payload(reader: _Reader, tag: int) -> Any:
    if tag == TAG_BYTE:
        return reader._unpack(">b", 1)
    if tag == TAG_SHORT:
        return reader._unpack(">h", 2)
    if tag == TAG_INT:
        return reader._unpack(">i", 4)
    if tag == TAG_LONG:
        return reader._unpack(">q", 8)
    if tag == TAG_FLOAT:
        return reader._unpack(">f", 4)
    if tag == TAG_DOUBLE:
        return reader._unpack(">d", 8)
    if tag == TAG_BYTE_ARRAY:
        length = reader._unpack(">i", 4)
        return list(reader.take(length))
    if tag == TAG_STRING:
        return reader.string()
    if tag == TAG_LIST:
        item_tag = reader.u1()
        length = reader._unpack(">i", 4)
        return [_read_payload(reader, item_tag) for _ in range(length)]
    if tag == TAG_COMPOUND:
        out: dict[str, Any] = {}
        while True:
            child_tag = reader.u1()
            if child_tag == TAG_END:
                break
            name = reader.string()
            out[name] = _read_payload(reader, child_tag)
        return out
    if tag == TAG_INT_ARRAY:
        length = reader._unpack(">i", 4)
        return [reader._unpack(">i", 4) for _ in range(length)]
    if tag == TAG_LONG_ARRAY:
        length = reader._unpack(">i", 4)
        return [reader._unpack(">q", 8) for _ in range(length)]
    raise ValueError(f"Unknown NBT tag id: {tag}")


def _decompress(raw: bytes) -> bytes:
    if raw[:2] == b"\x1f\x8b":  # gzip magic number
        return gzip.decompress(raw)
    if raw[:1] == b"\x78":  # zlib header
        try:
            return zlib.decompress(raw)
        except zlib.error:
            pass
    return raw


def parse(raw: bytes) -> dict[str, Any]:
    """Parse raw NBT bytes (gzip/zlib auto-detected) into a plain dict."""
    reader = _Reader(_decompress(raw))
    root_tag = reader.u1()
    if root_tag == TAG_END:
        return {}
    reader.string()  # root name (usually empty) — skip it
    payload = _read_payload(reader, root_tag)
    return payload if isinstance(payload, dict) else {"": payload}


def load(path: str | Path) -> dict[str, Any]:
    """Read and parse an NBT file (e.g. ``level.dat``)."""
    return parse(Path(path).read_bytes())


# --- writing -----------------------------------------------------------------


class _TypedArray(list[int]):
    """A list that remembers which NBT *array* tag it should be written as."""

    tag: int = TAG_INT_ARRAY


class ByteArray(_TypedArray):
    """Write as ``TAG_Byte_Array`` rather than a list of bytes."""

    tag = TAG_BYTE_ARRAY


class IntArray(_TypedArray):
    """Write as ``TAG_Int_Array`` — e.g. a chunk's biome data or a UUID."""

    tag = TAG_INT_ARRAY


class LongArray(_TypedArray):
    """Write as ``TAG_Long_Array`` — e.g. a section's packed block states."""

    tag = TAG_LONG_ARRAY


class Long(int):
    """Write as ``TAG_Long`` rather than the inferred ``TAG_INT``."""


class Byte(int):
    """Write as ``TAG_Byte`` — NBT's boolean, and many vanilla flags."""


class Short(int):
    """Write as ``TAG_Short``."""


class Float(float):
    """Write as ``TAG_Float`` rather than the inferred ``TAG_DOUBLE``."""


#: Exact-type dispatch for the wrappers above (checked before the general rules,
#: since each one subclasses a builtin that would otherwise match first).
_WRAPPER_TAGS: dict[type, int] = {
    Byte: TAG_BYTE,
    Short: TAG_SHORT,
    Long: TAG_LONG,
    Float: TAG_FLOAT,
    ByteArray: TAG_BYTE_ARRAY,
    IntArray: TAG_INT_ARRAY,
    LongArray: TAG_LONG_ARRAY,
}

#: Pack formats for the fixed-width numeric tags.
_NUMERIC_FORMATS: dict[int, str] = {
    TAG_BYTE: ">b",
    TAG_SHORT: ">h",
    TAG_INT: ">i",
    TAG_LONG: ">q",
    TAG_FLOAT: ">f",
    TAG_DOUBLE: ">d",
}

#: Element width of each array tag, and the format its members are packed with.
_ARRAY_FORMATS: dict[int, str] = {
    TAG_BYTE_ARRAY: ">b",
    TAG_INT_ARRAY: ">i",
    TAG_LONG_ARRAY: ">q",
}


def tag_of(value: Any) -> int:
    """The NBT tag id ``value`` will be written as.

    Wrapper classes win outright; otherwise the Python type decides. ``bool`` is
    checked before ``int`` because it is a subclass of it.
    """
    wrapper = _WRAPPER_TAGS.get(type(value))
    if wrapper is not None:
        return wrapper
    if isinstance(value, bool):
        return TAG_BYTE
    if isinstance(value, int):
        return TAG_INT
    if isinstance(value, float):
        return TAG_DOUBLE
    if isinstance(value, str):
        return TAG_STRING
    if isinstance(value, dict):
        return TAG_COMPOUND
    if isinstance(value, (list, tuple)):
        return TAG_LIST
    raise TypeError(f"cannot write {type(value).__name__} as NBT: {value!r}")


def _write_string(out: bytearray, text: str) -> None:
    encoded = text.encode("utf-8")
    out += struct.pack(">H", len(encoded))
    out += encoded


def _write_payload(out: bytearray, tag: int, value: Any) -> None:
    """Append the payload for ``value`` written as ``tag``."""
    if tag in _NUMERIC_FORMATS:
        out += struct.pack(_NUMERIC_FORMATS[tag], value)
        return
    if tag == TAG_STRING:
        _write_string(out, str(value))
        return
    if tag in _ARRAY_FORMATS:
        fmt = _ARRAY_FORMATS[tag]
        out += struct.pack(">i", len(value))
        for item in value:
            out += struct.pack(fmt, int(item))
        return
    if tag == TAG_LIST:
        items = list(value)
        # An NBT list is homogeneous: its element tag is declared once, up front.
        item_tag = tag_of(items[0]) if items else TAG_END
        out += struct.pack(">B", item_tag)
        out += struct.pack(">i", len(items))
        for item in items:
            _write_payload(out, item_tag, item)
        return
    if tag == TAG_COMPOUND:
        for key, item in value.items():
            item_tag = tag_of(item)
            out += struct.pack(">B", item_tag)
            _write_string(out, str(key))
            _write_payload(out, item_tag, item)
        out += b"\x00"  # TAG_End closes the compound
        return
    raise TypeError(f"cannot write NBT tag id {tag}")


def dump(data: dict[str, Any], *, name: str = "", gzipped: bool = True) -> bytes:
    """Serialise ``data`` as an NBT document — the inverse of :func:`parse`.

    ``name`` is the root compound's name, which vanilla leaves empty. Structure
    files and ``level.dat`` are gzip-compressed, so that is the default.
    """
    out = bytearray()
    out += struct.pack(">B", TAG_COMPOUND)
    _write_string(out, name)
    _write_payload(out, TAG_COMPOUND, data)
    raw = bytes(out)
    return gzip.compress(raw) if gzipped else raw


def save(
    data: dict[str, Any], path: str | Path, *, name: str = "", gzipped: bool = True
) -> Path:
    """Write ``data`` to ``path`` as an NBT file; return the path."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(dump(data, name=name, gzipped=gzipped))
    return destination


# --- validation --------------------------------------------------------------


def expect_nbt(path: str | Path, *, what: str = "NBT file") -> dict[str, Any]:
    """Read an NBT file, raising a readable error rather than a binary one.

    The NBT counterpart to
    :func:`grimmclub_filesystem.checks.expect_json`: existence and decodability
    are checked together, so there is no way to use an unvalidated file.

    A truncated or non-NBT file otherwise surfaces as a bare ``EOFError`` or a
    gzip ``BadGzipFile`` from deep inside the parser, which says nothing about
    *which* file is at fault.
    """
    target = expect_file(path, what=what, allow_empty=False)
    try:
        document = parse(target.read_bytes())
    except EOFError as error:
        raise ContentError(
            f"{what} ends unexpectedly — it is truncated or not NBT at all: "
            f"{target}\n  ({error})"
        ) from None
    except (ValueError, OSError, gzip.BadGzipFile, zlib.error) as error:
        raise ContentError(
            f"{what} is not readable as NBT: {target}\n  ({error})"
        ) from None
    if not isinstance(document, dict):
        raise ContentError(
            f"{what} does not hold an NBT compound at its root: {target}"
        )
    return document


def expect_keys(
    document: dict[str, Any], *keys: str, what: str = "NBT document"
) -> dict[str, Any]:
    """Require ``keys`` to be present, naming *all* the missing ones at once.

    Reporting them together matters: fixing a hand-edited file one error per run
    is what makes schema errors miserable.
    """
    missing = [key for key in keys if key not in document]
    if missing:
        present = ", ".join(sorted(document)) or "nothing"
        raise ContentError(
            f"{what} is missing {', '.join(missing)}\n  it holds: {present}"
        )
    return document
