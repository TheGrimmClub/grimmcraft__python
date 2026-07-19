"""Tests for grimmclub_filesystem.transfer (no real network calls)."""

from __future__ import annotations

import pytest

from grimmclub_filesystem import transfer


def test_suggest_filename():
    assert transfer.suggest_filename("https://host/path/world.zip") == "world.zip"
    assert transfer.suggest_filename("https://host/") == "download.bin"
    assert transfer.suggest_filename("https://host/", "fallback.zip") == "fallback.zip"


def test_download_rejects_unknown_scheme(tmp_path):
    with pytest.raises(ValueError):
        transfer.download("gopher://host/file", tmp_path / "x")


def test_fetch_rejects_unknown_kind(tmp_path):
    with pytest.raises(ValueError):
        transfer.fetch({"kind": "carrier-pigeon"}, tmp_path / "x")


def test_fetch_http_needs_url(tmp_path):
    with pytest.raises(ValueError):
        transfer.fetch({"kind": "http"}, tmp_path / "x")
