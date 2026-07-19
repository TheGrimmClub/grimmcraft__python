"""Integration tests for grimmclub_filesystem.transfer against real local servers.

These spin up a throwaway HTTP (stdlib) and FTP (pyftpdlib, dev dep) server on
localhost, so the download paths are exercised for real without touching the
network. FTP is skipped if pyftpdlib is not installed.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from grimmclub_filesystem import transfer


@pytest.fixture
def served_dir(tmp_path: Path) -> Path:
    """A directory with a sample payload to be served."""
    (tmp_path / "world.zip").write_bytes(b"PK\x03\x04 pretend-zip-bytes")
    return tmp_path


@pytest.fixture
def http_base(served_dir: Path):
    handler = partial(SimpleHTTPRequestHandler, directory=str(served_dir))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_http_download(http_base: str, tmp_path: Path, served_dir: Path):
    dest = tmp_path / "out" / "got.zip"
    result = transfer.http_download(f"{http_base}/world.zip", dest)
    assert result == dest
    assert dest.read_bytes() == (served_dir / "world.zip").read_bytes()


def test_fetch_http_dict(http_base: str, tmp_path: Path, served_dir: Path):
    dest = tmp_path / "fetched.zip"
    transfer.fetch({"kind": "http", "url": f"{http_base}/world.zip"}, dest)
    assert dest.read_bytes() == (served_dir / "world.zip").read_bytes()


def test_ftp_download(served_dir: Path, tmp_path: Path):
    pytest.importorskip("pyftpdlib")
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import FTPServer

    authorizer = DummyAuthorizer()
    authorizer.add_anonymous(str(served_dir))
    handler = FTPHandler
    handler.authorizer = authorizer
    server = FTPServer(("127.0.0.1", 0), handler)
    port = server.address[1]

    # Keep every socket operation (poll + close) inside the server thread to
    # avoid a cross-thread file-descriptor race on shutdown.
    stop = threading.Event()

    def serve() -> None:
        while not stop.is_set():
            server.serve_forever(timeout=0.2, blocking=False)
        server.close_all()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        dest = tmp_path / "ftp-out.zip"
        transfer.ftp_download("127.0.0.1", "/world.zip", dest, port=port)
        assert dest.read_bytes() == (served_dir / "world.zip").read_bytes()
    finally:
        stop.set()
        thread.join(timeout=3)
