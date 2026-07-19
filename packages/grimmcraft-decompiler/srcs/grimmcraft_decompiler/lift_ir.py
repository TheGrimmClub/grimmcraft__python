"""Level 1 — lift a datapack tree into the compiler's :class:`Datapack` IR.

This is the level that works for **any** datapack, grimmcraft-generated or not:
every ``.mcfunction`` becomes a :class:`Function` of declarative commands (with
anything unmodellable preserved verbatim as ``raw``), every ``tags/function``
list becomes a :class:`FunctionTag`, and every other JSON file becomes a
:class:`Resource`.

Function *comments* are kept as ``comment`` commands rather than being hoisted
into :attr:`Function.comment`.  Both render identically, and keeping them in the
command list means the lifter never has to guess whether a leading ``#`` was a
file header or a real line — the machine lifter reads them back out of the list.
"""

from __future__ import annotations

import json

from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.emit import _PLURALS, category_dir
from grimmcraft_compiler.ir import Datapack, Function, FunctionTag, Resource, ResourceLocation
from grimmcraft_control.machine import Command
from grimmcraft_decompiler.detect import Detection
from grimmcraft_decompiler.diagnostics import Codes, DiagnosticBag, at
from grimmcraft_decompiler.reader import CommandReader
from grimmcraft_decompiler.source import PackSource

#: Plural resource folder -> the singular category name the IR stores.
_SINGULARS = {plural: singular for singular, plural in _PLURALS.items()}

#: Folders under ``data/<ns>/`` that are not JSON resources.
_NON_RESOURCE_DIRS = {"function", "functions", "tags"}


def _singular_category(folder: str) -> str:
    """The IR category name for an on-disk resource folder.

    The emitter re-pluralises this for pre-1.21 targets, so storing the singular
    form is what lets a pack move between folder schemes.
    """
    if folder in _SINGULARS:
        return _SINGULARS[folder]
    return folder[:-1] if folder.endswith("s") else folder


def _pick_namespace(
    source: PackSource, function_dir: str, bag: DiagnosticBag
) -> str:
    """The pack's own namespace — the one holding its functions, not ``minecraft``.

    ``minecraft`` is excluded because every pack writes its ``load``/``tick`` tags
    there; it is a *host* namespace, never the pack's identity.
    """
    owners = {
        parts[1]
        for path in source.files
        if len(parts := path.split("/")) > 3
        and parts[0] == "data"
        and parts[1] != "minecraft"
        and parts[2] == function_dir
    }
    if len(owners) == 1:
        return owners.pop()
    if not owners:
        # Nothing but minecraft: a tags-only pack. Fall back to any namespace.
        namespaces = [ns for ns in source.namespaces if ns != "minecraft"]
        return namespaces[0] if namespaces else "minecraft"

    chosen = sorted(owners)[0]
    bag.emit(
        Codes.AMBIGUOUS_NAMESPACE,
        f"the pack defines functions in several namespaces "
        f"({', '.join(sorted(owners))}); treating '{chosen}' as the pack namespace",
        hint="the namespace only labels the pack; every function keeps its own",
        source=source.label,
    )
    return chosen


def _read_function(
    source: PackSource, path: str, function_dir: str, reader: CommandReader
) -> Function | None:
    """Lift one ``.mcfunction`` file into a :class:`Function`."""
    parts = path.split("/")
    # data/<ns>/<function_dir>/<nested/path>.mcfunction
    if len(parts) < 4 or parts[0] != "data" or parts[2] != function_dir:
        return None
    namespace = parts[1]
    relative = "/".join(parts[3:]).removesuffix(".mcfunction")
    text = source.files[path]

    commands: list[Command] = []
    # splitlines() drops the trailing newline the emitter adds; a genuinely
    # blank line in the middle survives as a raw empty command.
    for number, line in enumerate(text.splitlines(), start=1):
        commands.append(reader.read(line, source=at(path, number)))

    return Function(ResourceLocation(namespace, relative), commands)


def _read_tag(source: PackSource, path: str, function_dir: str) -> FunctionTag | None:
    """Lift one ``tags/<function_dir>/*.json`` file into a :class:`FunctionTag`."""
    parts = path.split("/")
    # data/<ns>/tags/<function_dir>/<nested/path>.json
    if len(parts) < 5 or parts[0] != "data" or parts[2] != "tags" or parts[3] != function_dir:
        return None
    try:
        document = json.loads(source.files[path])
    except json.JSONDecodeError:
        return None
    if not isinstance(document, dict):
        return None
    values = document.get("values")
    if not isinstance(values, list):
        return None

    namespace = parts[1]
    relative = "/".join(parts[4:]).removesuffix(".json")
    members = [
        ResourceLocation.parse(value) for value in values if isinstance(value, str)
    ]
    return FunctionTag(ResourceLocation(namespace, relative), members)


def _read_resource(source: PackSource, path: str, function_dir: str) -> Resource | None:
    """Lift a non-function, non-tag JSON file into a :class:`Resource`."""
    parts = path.split("/")
    if len(parts) < 4 or parts[0] != "data" or not path.endswith(".json"):
        return None
    folder = parts[2]
    if folder in _NON_RESOURCE_DIRS or folder == function_dir:
        return None
    try:
        content = json.loads(source.files[path])
    except json.JSONDecodeError:
        return None
    if not isinstance(content, dict):
        return None

    relative = "/".join(parts[3:]).removesuffix(".json")
    return Resource(
        ResourceLocation(parts[1], relative), _singular_category(folder), content
    )


def lift_ir(
    source: PackSource, detection: Detection, bag: DiagnosticBag
) -> Datapack:
    """Parse ``source`` into a :class:`Datapack` IR for the detected target.

    Never fails: files that cannot be understood are reported through ``bag`` and
    either preserved as ``raw`` commands or skipped, so the caller always gets a
    usable pack back.
    """
    info = detection.info
    function_dir = category_dir("function", info)
    reader = CommandReader(detection.target, bag)

    namespace = _pick_namespace(source, function_dir, bag)
    pack = Datapack(namespace=namespace, description=detection.description)

    if not any(path.startswith("data/") for path in source.files):
        bag.emit(
            Codes.NO_DATA_DIRECTORY,
            "the pack has no 'data/' directory, so it defines nothing",
            hint="a datapack stores everything under data/<namespace>/…",
            source=source.label,
        )
        return pack

    for path in source.paths_under("data/", ".mcfunction"):
        function = _read_function(source, path, function_dir, reader)
        if function is not None:
            pack.add_function(function)

    for path in source.paths_under("data/", ".json"):
        tag = _read_tag(source, path, function_dir)
        if tag is not None:
            pack.tags.append(tag)
            continue
        resource = _read_resource(source, path, function_dir)
        if resource is not None:
            pack.resources.append(resource)

    return pack


def render_ir(pack: Datapack, detection: Detection) -> str:
    """A readable text dump of the IR — what ``--emit ir`` prints.

    Deliberately not valid Python: this is the "what did the parser actually
    see" view, used to inspect any pack, including ones no machine can be lifted
    from.
    """
    dialect = Dialect(detection.target)
    lines: list[str] = [
        f"# datapack '{pack.namespace}' for {detection.target}",
        f"# description: {pack.description}",
        f"# {len(pack.functions)} function(s), {len(pack.tags)} tag(s), "
        f"{len(pack.resources)} resource(s)",
        "",
    ]
    for function in pack.functions:
        lines.append(f"function {function.id}:")
        for command in function.commands:
            lines.append(f"    {command.name:<24} {_summarise(command, dialect)}")
        lines.append("")
    for tag in pack.tags:
        members = ", ".join(str(value) for value in tag.values)
        lines.append(f"tag {tag.id}: [{members}]")
    for resource in pack.resources:
        lines.append(f"resource {resource.id} ({resource.category})")
    return "\n".join(lines).rstrip() + "\n"


def _summarise(command: Command, dialect: Dialect) -> str:
    """One-line payload summary for the IR dump, falling back to the payload dict."""
    try:
        return dialect.render(command)
    except (ValueError, KeyError, TypeError):
        return str(dict(command.payload))
