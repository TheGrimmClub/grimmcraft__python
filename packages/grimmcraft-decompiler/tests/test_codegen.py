"""Generated Python must be real, runnable source — not a pretty approximation.

The strongest statement available: execute the generated module, rebuild the
machines it describes, compile *those*, and require the result to match the pack
we started from byte for byte.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from grimmcraft_control.demos import door_machine, furnace_machine
from grimmcraft_decompiler import decompile
from grimmcraft_decompiler.roundtrip import Level, roundtrip

from .conftest import VERSIONS, build_pack


def generated(path: Path) -> str:
    result = decompile(path, emit="python")
    with result.source:
        return result.output


@pytest.mark.parametrize("version", VERSIONS)
def test_generated_python_parses(tmp_path: Path, version: str) -> None:
    pack = build_pack([door_machine(), furnace_machine()], tmp_path / "p", version)
    ast.parse(generated(pack))


def test_generated_python_uses_the_builder_api(tmp_path: Path) -> None:
    pack = build_pack([door_machine()], tmp_path / "p", "1.21.11")
    source = generated(pack)
    assert "new_machine('door')" in source
    assert "builder.add_state('CLOSED')" in source
    assert "builder.initial(" in source
    assert ".enter.setblock(" in source


def test_generated_python_uses_with_blocks(tmp_path: Path) -> None:
    """Output should read like the hand-written examples, which group with `with`."""
    pack = build_pack([door_machine(), furnace_machine()], tmp_path / "p", "1.21.11")
    source = generated(pack)
    # OPEN carries enter/exit effects, so it gets a block; a state whose effects
    # all landed on its transitions stays a plain assignment (tested below).
    assert "with builder.add_state('OPEN') as state_open:" in source
    assert "with builder.add_transition(" in source


def test_generated_variables_do_not_shadow_builtins(tmp_path: Path) -> None:
    """A state named OPEN must not bind `open` in the generated module."""
    pack = build_pack([door_machine()], tmp_path / "p", "1.21.11")
    source = generated(pack)
    assert "as state_open:" in source
    assert "\n    open = " not in source and " as open:" not in source


def test_states_with_no_effects_stay_a_plain_assignment(tmp_path: Path) -> None:
    """A `with` block over an empty body would need a `pass` — emit a binding instead."""
    from grimmcraft_control import new_machine

    builder = new_machine("bare")
    first = builder.add_state("A")  # no effects at all
    second = builder.add_state("B")
    builder.transition(first, "go", to=second)
    builder.initial(first)

    source = generated(build_pack([builder.build()], tmp_path / "p", "1.21.11"))
    ast.parse(source)
    assert "a = builder.add_state('A')" in source
    assert "with builder.add_state('A')" not in source


def test_repeated_guards_collapse_into_one_with_block(tmp_path: Path) -> None:
    """Consecutive effects sharing an if_score guard write the condition once."""
    from grimmcraft_control import new_machine

    builder = new_machine("tree")
    with builder.add_state("GROWING") as growing:
        with growing.cycle.if_score("stage", "tree", 1) as guarded:
            guarded.say("one")
            guarded.say("two")
        growing.cycle.if_score("stage", "tree", 2).say("alone")
    builder.initial(growing)

    source = generated(build_pack([builder.build()], tmp_path / "p", "1.21.11"))
    ast.parse(source)
    assert "with growing.cycle.if_score('stage', 'tree', 1) as guarded:" in source
    # A lone guarded effect reads better chained than as a one-line block.
    assert "growing.cycle.if_score('stage', 'tree', 2).say('alone')" in source


def test_generated_python_emits_declarative_guards(tmp_path: Path) -> None:
    pack = build_pack([furnace_machine()], tmp_path / "p", "1.21.11")
    source = generated(pack)
    assert "TICK_EVENT" in source
    assert ".when_score('furnace_timer', 'furnace', 0)" in source


def run_module(source: str, tmp_path: Path) -> dict[str, Any]:
    """Execute generated source in a fresh namespace and return it."""
    namespace: dict[str, Any] = {"__name__": "generated"}
    exec(compile(source, "<generated>", "exec"), namespace)  # noqa: S102
    return namespace


@pytest.mark.parametrize("version", VERSIONS)
def test_generated_python_rebuilds_an_identical_pack(
    tmp_path: Path, version: str
) -> None:
    """The payoff: run the generated code and get the original datapack back."""
    original = build_pack(
        [door_machine(), furnace_machine()], tmp_path / "p", version
    )
    result = decompile(original, emit="python")

    namespace = run_module(result.output, tmp_path)
    rebuilt = [
        value()
        for name, value in namespace.items()
        if name.startswith("build_") and callable(value)
    ]
    assert len(rebuilt) == 2

    with result.source:
        report = roundtrip(
            result.source,
            result.pack,
            result.target,
            machines=rebuilt,
            level=Level.MACHINE,
        )
        assert report.identical, report.render()


def test_generated_python_records_the_target(tmp_path: Path) -> None:
    """The module must pin the version it came from, or recompiling drifts."""
    pack = build_pack([door_machine()], tmp_path / "p", "1.20.4")
    namespace = run_module(generated(pack), tmp_path)
    assert namespace["VERSION"] == "1.20.4"
    assert namespace["FLAVOR"] == "vanilla"
    assert namespace["NAMESPACE"] == "test"


def test_state_names_that_are_not_identifiers_are_handled(tmp_path: Path) -> None:
    """A state called 'not a name!' still yields valid Python."""
    from grimmcraft_control import new_machine

    builder = new_machine("odd")
    first = builder.add_state("not a name!")
    second = builder.add_state("class")  # a Python keyword
    builder.transition(first, "go", to=second)
    builder.initial(first)

    pack = build_pack([builder.build()], tmp_path / "p", "1.21.11")
    source = generated(pack)
    ast.parse(source)
    assert "'not a name!'" in source
