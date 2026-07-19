"""Download data from the internet — a gentle interface to FTP and HTTP(S).

The goal is learnability: one obvious function per idea, friendly names, and
a single :func:`fetch` that reads a small dict so a beginner can describe a
source in YAML instead of remembering library APIs.
"""

# Includes internal
# Includes standard
import ftplib
import shutil
import urllib.request
from typing import Any
from urllib.parse import urlparse

from grimmclub_filesystem.core import SystemPath, path_like
from grimmclub_filesystem.paths import as_path, ensure_dir


def _prepare(path: path_like) -> SystemPath:
    """Convert to a :class:`SystemPath`, ensuring its parent directory exists."""
    path = as_path(path)
    ensure_dir(path.parent)
    return path


def http_download(from_url: str, to_path: path_like) -> SystemPath:
    """Download an ``http://`` or ``https://`` URL to ``to_path``."""
    to_path = _prepare(to_path)
    request = urllib.request.Request(from_url, headers={"User-Agent": "grimm-guard"})
    with urllib.request.urlopen(request) as response, open(to_path, "wb") as out:
        shutil.copyfileobj(response, out)
    return to_path


def ftp_download(
    host: str,
    remote_path: str,
    to_path: path_like,
    *,
    user: str = "anonymous",
    password: str = "",
    port: int = 21,
) -> SystemPath:
    """Download a single file from an FTP server to ``to_path``."""
    to_path = _prepare(to_path)
    with ftplib.FTP() as ftp:
        ftp.connect(host, port)
        ftp.login(user, password)
        with open(to_path, "wb") as out:
            ftp.retrbinary(f"RETR {remote_path}", out.write)
    return to_path


def _ftp_from_url(from_url: str, to_path: path_like) -> SystemPath:
    """Download a file from an FTP URL to ``to_path``."""
    parts = urlparse(from_url)
    if not parts.hostname:
        raise ValueError(f"FTP url has no host: {from_url}")
    return ftp_download(
        parts.hostname,
        parts.path,
        to_path,
        user=parts.username or "anonymous",
        password=parts.password or "",
        port=parts.port or 21,
    )


def download(from_url: str, to_path: path_like) -> SystemPath:
    """Download any supported URL (``http``, ``https`` or ``ftp``) to ``to_path``."""
    scheme = urlparse(from_url).scheme.lower()
    if scheme in ("http", "https"):
        return http_download(from_url, to_path)
    if scheme == "ftp":
        return _ftp_from_url(from_url, to_path)
    raise ValueError(f"Don't know how to download a '{scheme}' url: {from_url}")


def suggest_filename(url: str, fallback: str = "download.bin") -> str:
    """Guess a sensible filename from the tail of a URL."""
    name = SystemPath(urlparse(url).path).name
    return name or fallback


def fetch(source: dict[str, Any], to_path: path_like) -> SystemPath:
    """Download from a *source description* (a small dict, e.g. from YAML).

    Supported shapes::

        {kind: http,  url: "https://host/world.zip"}
        {kind: ftp,   url: "ftp://user:pass@host/path/world.zip"}
        {kind: ftp,   host: host, path: /world.zip, user: me, password: pw, port: 21}

    ``kind`` is optional when a ``url`` is given (it is read from the scheme).
    """
    url = source.get("url")
    kind = (source.get("kind") or (urlparse(url).scheme if url else "")).lower()

    match kind:
        case "http" | "https":
            if not url:
                raise ValueError("http source needs a 'url'")
            return http_download(url, to_path)
        case "ftp":
            if url:
                return _ftp_from_url(url, to_path)
            return ftp_download(
                source["host"],
                source["path"],
                to_path,
                user=source.get("user", "anonymous"),
                password=source.get("password", ""),
                port=int(source.get("port", 21)),
            )
        case _:
            raise ValueError(f"Unknown source kind: {kind!r} (use 'http', 'https' or 'ftp')")
