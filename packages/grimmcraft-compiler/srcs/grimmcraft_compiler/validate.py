"""Validation against ``grimmcraft-data`` and the IR, producing diagnostics.

Two passes:

* :func:`validate_machines` walks the machines' declarative commands and checks
  every referenced ``Block``/``Item``/``Entity`` id (existence, historic renames,
  deprecations, "did you mean" suggestions), flavor/version portability, and
  whether runtime guards can be compiled.
* :func:`validate_ir` checks the lowered pack: resource-location character rules,
  and that every ``function`` call and function-tag member resolves inside the
  pack.

Both append to a shared :class:`DiagnosticBag`; nothing here aborts on its own.
"""

from __future__ import annotations

from typing import Any

from grimmcraft_compiler import registry
from grimmcraft_compiler.diagnostics import Codes, DiagnosticBag, Severity
from grimmcraft_compiler.ir import Datapack, Function, ResourceLocation
from grimmcraft_compiler.target import Flavor, Target
from grimmcraft_compiler.version import parse_version
from grimmcraft_control.machine import Command, Machine

# command name -> (payload key, registry kind) for id-bearing commands.
_ID_FIELDS: dict[str, tuple[str, str]] = {
    "setblock": ("block", "block"),
    "fill": ("block", "block"),
    "summon": ("entity", "entity"),
    "give": ("item", "item"),
}


def _check_id(
    kind: str, value: object, version: str, source: str, bag: DiagnosticBag
) -> None:
    """Validate one id reference (skip enum members — they are valid by origin)."""
    if not isinstance(value, str):
        # An enum member from grimmcraft_data: valid by construction. Still flag
        # deprecation on its string id.
        string_id = getattr(value, "string_id", None)
        if isinstance(string_id, str):
            _check_deprecation(string_id, source, bag)
        return

    string_id = value if ":" in value else f"minecraft:{value}"
    if registry.exists(kind, string_id):
        _check_deprecation(string_id, source, bag)
        return

    # Unknown id — build the most helpful message we can.
    rename = registry.rename_of(string_id)
    suggestions = registry.suggest(kind, string_id)
    parts = [f"{kind} '{string_id}' does not exist in {version}."]
    hint_parts: list[str] = []
    if rename is not None:
        parts.append(
            f"It was renamed to '{rename.new}' in {rename.since}."
        )
        hint_parts.append(f"use '{rename.new}'")
    if suggestions:
        parts.append(f"Did you mean '{suggestions[0]}'?")
        if not hint_parts:
            hint_parts.append(f"use '{suggestions[0]}'")
    bag.emit(
        Codes.UNKNOWN_ID,
        " ".join(parts),
        hint="; ".join(hint_parts) or f"check the {kind} id spelling",
        source=source,
    )


def _check_deprecation(string_id: str, source: str, bag: DiagnosticBag) -> None:
    reason = registry.deprecation_of(string_id)
    if reason:
        bag.emit(
            Codes.DEPRECATED_ID,
            f"'{string_id}' is deprecated: {reason}",
            hint="prefer a non-technical block/item",
            source=source,
        )


def _check_portability(
    command: Command, target: Target, source: str, bag: DiagnosticBag
) -> None:
    """Flavor- and version-portability checks driven by declarative payload flags."""
    payload = command.payload

    # Version gate: a command may declare a minimum version.
    min_version = payload.get("min_version")
    if isinstance(min_version, str) and parse_version(min_version) > target.info.version_tuple:
        bag.emit(
            Codes.UNAVAILABLE_FEATURE,
            f"command '{command.name}' requires Minecraft {min_version} or newer, "
            f"but the target is {target.version}",
            hint=f"target {min_version}+ or remove this command",
            source=source,
        )

    # Explicit component data on a pre-1.20.5 target: the NBT/components split.
    if payload.get("components") is not None and not target.info.uses_components:
        bag.emit(
            Codes.UNAVAILABLE_FEATURE,
            "item/block components are only available from 1.20.5; before that, "
            f"data must be written as NBT tags (target is {target.version})",
            hint="target 1.20.5+ or express this data as NBT",
            source=source,
        )

    # Flavor gate: a command may require a specific flavor.
    requires_flavor = payload.get("requires_flavor")
    if isinstance(requires_flavor, str) and requires_flavor != target.flavor.value:
        bag.emit(
            Codes.FLAVOR_MISMATCH,
            f"command '{command.name}' is meaningful on {requires_flavor}, "
            f"but the target flavor is {target.flavor.value}",
            hint=f"compile with --flavor {requires_flavor} or use a vanilla equivalent",
            source=source,
        )

    if payload.get("requires_mod_api") and target.flavor is Flavor.FABRIC:
        bag.emit(
            Codes.FLAVOR_MISMATCH,
            f"command '{command.name}' needs a Fabric mod API and cannot run from a "
            "pure datapack",
            hint="provide this behaviour via a Fabric mod, or drop the command",
            source=source,
        )


def _walk_command(
    command: Command, target: Target, source: str, bag: DiagnosticBag
) -> None:
    field = _ID_FIELDS.get(command.name)
    if field is not None:
        key, kind = field
        if key in command.payload:
            _check_id(kind, command.payload[key], target.version, source, bag)
    _check_portability(command, target, source, bag)


def validate_machines(
    machines: list[Machine[Any]], target: Target, bag: DiagnosticBag
) -> None:
    """Validate every machine's declarative commands, guards and conditions."""
    for machine in machines:
        if not machine.transitions:
            bag.emit(
                Codes.EMPTY_MACHINE,
                f"machine '{machine.name}' has no transitions; it will do nothing",
                hint="add at least one transition, or remove the machine",
                source=machine.name,
            )
        for state_name, state in machine.states.items():
            for phase, group in (("enter", state.enter), ("exit", state.exit),
                                 ("cycle", state.cycle)):
                for command in group:
                    _walk_command(
                        command, target, f"{machine.name}:{state_name}.{phase}", bag
                    )
        for t in machine.transitions:
            edge = f"{machine.name}:{t.source}--{t.event}-->{t.target}"
            for command in t.commands:
                _walk_command(command, target, edge, bag)
            if t.guard is not None and t.condition is None:
                bag.emit(
                    Codes.NON_COMPILABLE_GUARD,
                    f"transition {edge} has a Python guard that cannot be compiled; "
                    "it will be emitted as an unconditional transition",
                    hint="add a declarative Condition (e.g. score_matches) to guard it "
                    "in the datapack",
                    source=edge,
                )
            if t.condition is not None and t.condition.name != "score_matches":
                bag.emit(
                    Codes.UNKNOWN_COMMAND,
                    f"transition {edge} uses unknown condition "
                    f"'{t.condition.name}'; it cannot be lowered",
                    hint="use a supported condition kind (score_matches)",
                    source=edge,
                )


def _resolve_calls(function: Function, known: set[str], bag: DiagnosticBag) -> None:
    """Report any ``call`` (including nested in ``execute_if_score``) that dangles."""

    def check(command: Command) -> None:
        if command.name == "call":
            ref = command.payload["ref"]
            if ref not in known:
                bag.emit(
                    Codes.UNRESOLVED_FUNCTION,
                    f"function '{function.id}' calls '{ref}', which the pack does "
                    "not define",
                    hint="check the callee id, or ensure it is emitted",
                    source=str(function.id),
                )
        run = command.payload.get("run")
        if isinstance(run, Command):
            check(run)

    for command in function.commands:
        check(command)


def _check_location(location: ResourceLocation, source: str, bag: DiagnosticBag) -> None:
    reason = location.invalid_reason()
    if reason is not None:
        bag.emit(
            Codes.INVALID_RESOURCE_LOCATION,
            f"invalid resource location '{location}': {reason}",
            hint="use only the allowed characters shown above",
            source=source,
        )


def validate_ir(pack: Datapack, bag: DiagnosticBag) -> None:
    """Validate resource locations and that all function references resolve."""
    known = pack.function_ids()

    for function in pack.functions:
        _check_location(function.id, str(function.id), bag)
        _resolve_calls(function, known, bag)

    for tag in pack.tags:
        _check_location(tag.id, f"tag {tag.id}", bag)
        for member in tag.values:
            if str(member) not in known:
                bag.emit(
                    Codes.UNRESOLVED_TAG_MEMBER,
                    f"function tag '{tag.id}' references '{member}', which the pack "
                    "does not define",
                    hint="remove the member or emit the function it names",
                    source=f"tag {tag.id}",
                )

    for resource in pack.resources:
        _check_location(resource.id, f"{resource.category} {resource.id}", bag)


# ``Severity`` re-exported for callers that build diagnostics off validation.
__all__ = ["validate_machines", "validate_ir", "Severity"]
