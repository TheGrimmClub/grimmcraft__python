"""Read the interesting facts out of a Minecraft world folder."""

# [ ] Includes internal
# [ ] Includes standard
import json
from dataclasses import dataclass, field
from typing import Any

# [ ] Includes external
from grimmclub_filesystem.core import SystemPath, SystemPathOptional, path_like
from grimmclub_filesystem.paths import as_path, locate_directory
from grimmcraft_world import nbt


# [ ] Classes
@dataclass
class Datapack:
    """One datapack found inside ``world/datapacks``."""

    name: str
    description: str = ""
    enabled: bool = True


@dataclass
class WorldInfo:
    """A friendly summary of a world, used for naming backups and docs."""

    path: SystemPath
    name: str
    version: str
    data_version: int | None = None
    datapacks: list[Datapack] = field(default_factory=list)


# [ ] Functions
#
def locate_world(root: path_like) -> SystemPathOptional:
    """Find a Minecraft world (a folder containing ``level.dat``) under ``root``.

    Thin, Minecraft-aware wrapper over :func:`grimmclub_filesystem.paths.locate_directory`.
    """
    return locate_directory(root, "level.dat")


def _get(data: dict[str, Any], *names: str, default: Any = None) -> Any:
    """Case-insensitive nested lookup, tolerant of NBT capitalisation drift."""
    current = data
    for name in names:
        if not isinstance(current, dict):
            return default
        found = None
        for key in current:
            if key.lower() == name.lower():
                found = key
                break
        if found is None:
            return default
        current = current[found]
    return current


def discover_datapacks(world_dir: path_like, enabled: set[str] | None = None) -> list[Datapack]:
    """List datapacks under ``world/datapacks`` (reads each ``pack.mcmeta``)."""
    packs_dir = as_path(world_dir) / "datapacks"
    packs: list[Datapack] = []
    if not packs_dir.is_dir():
        return packs
    for entry in sorted(packs_dir.iterdir()):
        meta = entry / "pack.mcmeta"
        if not (entry.is_dir() and meta.is_file()):
            continue
        description = ""
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            description = str(data.get("pack", {}).get("description", ""))
        except (json.JSONDecodeError, OSError):
            pass
        # level.dat lists enabled packs as "file/<name>"; older worlds use the
        # bare name, so accept either.
        is_enabled = enabled is None or (
            f"file/{entry.name}" in enabled or entry.name in enabled
        )
        packs.append(
            Datapack(name=entry.name, description=description, enabled=is_enabled)
        )
    return packs


def read_world_info(world_dir: path_like) -> WorldInfo:
    """Read ``level.dat`` + datapacks and return a :class:`WorldInfo`."""
    world = as_path(world_dir)
    level = world / "level.dat"
    if not level.is_file():
        raise FileNotFoundError(f"No level.dat in {world} — is this a world folder?")

    data = _get(nbt.load(level), "Data", default={})
    version = _get(data, "Version", "Name", default="unknown")
    name = _get(data, "LevelName", default=world.name)
    data_version = _get(data, "DataVersion")
    enabled = _get(data, "DataPacks", "Enabled")
    enabled_set = set(enabled) if isinstance(enabled, list) else None

    return WorldInfo(
        path=world,
        name=str(name),
        version=str(version),
        data_version=int(data_version) if isinstance(data_version, int) else None,
        datapacks=discover_datapacks(world, enabled_set),
    )
