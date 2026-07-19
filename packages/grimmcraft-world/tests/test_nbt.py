"""Tests for the built-in NBT reader, against a real level.dat fixture."""

from __future__ import annotations

import gzip
import struct
from pathlib import Path

from grimmcraft_world import nbt


def _encode_compound(pairs: list[tuple[int, str, bytes]]) -> bytes:
    """Tiny helper: build a TAG_Compound payload from (tag, name, payload)."""
    out = b""
    for tag, name, payload in pairs:
        out += bytes([tag]) + struct.pack(">H", len(name)) + name.encode() + payload
    return out + b"\x00"  # TAG_End


def test_parse_roundtrip_simple():
    # a root compound holding an int and a string
    int_payload = struct.pack(">i", 42)
    str_payload = struct.pack(">H", 3) + b"hey"
    body = _encode_compound(
        [(nbt.TAG_INT, "Answer", int_payload), (nbt.TAG_STRING, "Greeting", str_payload)]
    )
    raw = bytes([nbt.TAG_COMPOUND]) + struct.pack(">H", 0) + body  # unnamed root
    parsed = nbt.parse(raw)
    assert parsed == {"Answer": 42, "Greeting": "hey"}


def test_parse_handles_gzip():
    body = _encode_compound([(nbt.TAG_STRING, "X", struct.pack(">H", 2) + b"ok")])
    raw = bytes([nbt.TAG_COMPOUND]) + struct.pack(">H", 0) + body
    assert nbt.parse(gzip.compress(raw)) == {"X": "ok"}


def test_load_real_level_dat(sample_world: Path):
    data = nbt.load(sample_world / "level.dat")
    assert "Data" in data
    level = data["Data"]
    assert level["LevelName"] == "world"
    assert level["Version"]["Name"] == "1.21.11"
    assert isinstance(level["DataVersion"], int)
