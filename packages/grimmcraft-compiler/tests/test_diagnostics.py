"""Diagnostics: unknown ids + suggestions, renames, strict mode, refs, locations."""

from __future__ import annotations

from typing import Any

from grimmcraft_compiler import Target, compile_machines
from grimmcraft_compiler.diagnostics import Codes, DiagnosticBag, Severity
from grimmcraft_compiler.ir import Datapack, Function, FunctionTag, ResourceLocation
from grimmcraft_compiler.validate import validate_ir, validate_machines
from grimmcraft_control.machine import Command, MachineBuilder


def _machine_with(*commands: Command) -> Any:
    return (
        MachineBuilder[dict[str, Any]]({})
        .named("test")
        .state("A")
        .state("B")
        .transition("A", "go", to="B", commands=commands)
        .initial("A")
        .build()
    )


def _codes(bag: DiagnosticBag) -> set[str]:
    return {d.code.id for d in bag}


def test_unknown_id_gets_code_and_suggestion() -> None:
    m = _machine_with(Command("setblock", {"pos": (0, 0, 0), "block": "minecraft:stoen"}))
    bag = DiagnosticBag()
    validate_machines([m], Target.resolve("1.21.1", "vanilla"), bag)
    errors = [d for d in bag if d.code is Codes.UNKNOWN_ID]
    assert len(errors) == 1
    assert "minecraft:stone" in errors[0].message
    assert errors[0].severity is Severity.ERROR


def test_rename_detection_grass() -> None:
    m = _machine_with(Command("setblock", {"pos": (0, 0, 0), "block": "minecraft:grass"}))
    bag = DiagnosticBag()
    validate_machines([m], Target.resolve("1.21.1", "vanilla"), bag)
    msg = next(d.message for d in bag if d.code is Codes.UNKNOWN_ID)
    assert "renamed to 'minecraft:short_grass'" in msg
    assert "1.20.3" in msg


def test_flavor_mismatch_warns() -> None:
    m = _machine_with(Command("say", {"text": "hi", "requires_flavor": "paper"}))
    bag = DiagnosticBag()
    validate_machines([m], Target.resolve("1.21.1", "vanilla"), bag)
    assert Codes.FLAVOR_MISMATCH.id in _codes(bag)


def test_components_before_1_20_5_is_error() -> None:
    m = _machine_with(Command("give", {"item": "minecraft:stone", "components": {"x": 1}}))
    bag = DiagnosticBag()
    validate_machines([m], Target.resolve("1.20.4", "vanilla"), bag)
    assert Codes.UNAVAILABLE_FEATURE.id in _codes(bag)


def test_unresolved_function_reference() -> None:
    pack = Datapack(namespace="grimmcraft", description="d")
    fn = Function(ResourceLocation("grimmcraft", "a"))
    fn.add(Command("call", {"ref": "grimmcraft:missing"}))
    pack.add_function(fn)
    bag = DiagnosticBag()
    validate_ir(pack, bag)
    assert Codes.UNRESOLVED_FUNCTION.id in _codes(bag)


def test_unresolved_tag_member() -> None:
    pack = Datapack(namespace="grimmcraft", description="d")
    pack.tags.append(
        FunctionTag(ResourceLocation("minecraft", "load"),
                    [ResourceLocation("grimmcraft", "nope")])
    )
    bag = DiagnosticBag()
    validate_ir(pack, bag)
    assert Codes.UNRESOLVED_TAG_MEMBER.id in _codes(bag)


def test_invalid_namespace_is_error() -> None:
    result = compile_machines(
        [_machine_with(Command("say", {"text": "hi"}))],
        Target.resolve("1.21.1", "vanilla"),
        namespace="Bad NS",
        dry_run=True,
    )
    assert not result.ok
    assert Codes.INVALID_RESOURCE_LOCATION.id in _codes(result.diagnostics)


def test_strict_promotes_warnings_to_errors() -> None:
    m = _machine_with(Command("say", {"text": "hi", "requires_flavor": "paper"}))
    target = Target.resolve("1.21.1", "vanilla")
    lenient = compile_machines([m], target, dry_run=True)
    assert lenient.ok  # a warning, but not an error
    strict = compile_machines([m], target, dry_run=True, strict=True)
    assert not strict.ok  # promoted to an error


def test_non_compilable_guard_warns() -> None:
    m = (
        MachineBuilder[dict[str, Any]]({})
        .named("g")
        .state("A")
        .state("B")
        .transition("A", "go", to="B", guard=lambda ctx, e: True)
        .initial("A")
        .build()
    )
    bag = DiagnosticBag()
    validate_machines([m], Target.resolve("1.21.1", "vanilla"), bag)
    assert Codes.NON_COMPILABLE_GUARD.id in _codes(bag)
