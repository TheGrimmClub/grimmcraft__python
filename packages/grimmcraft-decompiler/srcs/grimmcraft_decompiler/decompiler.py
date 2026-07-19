"""The decompiler pipeline: load → detect → IR → machines → emit.

Mirrors :func:`grimmcraft_compiler.compiler.compile_machines`: one call runs
everything, collects diagnostics rather than raising, and hands back a result
object carrying every intermediate level so a caller can take whichever it needs.

Each level degrades into the one below it.  A pack that is not a grimmcraft pack
still yields the IR; a pack whose ``pack_format`` is unknown still yields
functions.  Only an unreadable input is fatal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from grimmcraft_compiler.diagnostics import Severity
from grimmcraft_compiler.ir import Datapack
from grimmcraft_compiler.target import Flavor, Target
from grimmcraft_control.machine import Machine
from grimmcraft_decompiler.codegen import generate_python
from grimmcraft_decompiler.detect import Detection, detect_target
from grimmcraft_decompiler.diagnostics import Codes, DiagnosticBag
from grimmcraft_decompiler.lift_ir import lift_ir, render_ir
from grimmcraft_decompiler.lift_machine import lift_machines
from grimmcraft_decompiler.roundtrip import DiffReport, Level, roundtrip
from grimmcraft_decompiler.source import PackSource, open_pack

#: The reconstruction levels ``--emit`` can ask for.
EMIT_LEVELS = ("ir", "machine", "python")


@dataclass(slots=True)
class DecompileResult:
    """Everything a decompile produced, at every level that succeeded."""

    source: PackSource
    detection: Detection
    pack: Datapack
    diagnostics: DiagnosticBag
    machines: list[Machine[Any]] = field(default_factory=list)
    #: The rendered output for the requested ``emit`` level.
    output: str = ""
    output_path: Path | None = None
    diff: DiffReport | None = None

    @property
    def target(self) -> Target:
        return self.detection.target

    @property
    def ok(self) -> bool:
        """True when no errors were recorded."""
        return not self.diagnostics.has_errors

    @property
    def liftable(self) -> bool:
        """True when at least one machine was reconstructed."""
        return bool(self.machines)


def decompile(
    path: Path | str,
    *,
    emit: str = "python",
    version: str | None = None,
    flavor: Flavor | str = Flavor.VANILLA,
    output: Path | None = None,
    strict: bool = False,
    force: bool = False,
    dry_run: bool = False,
    check_roundtrip: bool = False,
) -> DecompileResult:
    """Decompile the datapack at ``path`` to the requested ``emit`` level.

    ``emit`` is one of :data:`EMIT_LEVELS`.  ``machine`` and ``python`` need a
    grimmcraft-generated pack; when reconstruction fails the result falls back to
    the IR and says why (``GD3001``).  ``strict`` promotes warnings to errors;
    ``force`` writes output even so; ``dry_run`` writes nothing.
    """
    if emit not in EMIT_LEVELS:
        raise ValueError(
            f"unknown emit level {emit!r}; choose one of: {', '.join(EMIT_LEVELS)}"
        )

    bag = DiagnosticBag()
    source = open_pack(path)
    detection = detect_target(source, bag, override=version, flavor=flavor)
    pack = lift_ir(source, detection, bag)

    machines: list[Machine[Any]] = []
    if emit in ("machine", "python"):
        machines = lift_machines(pack, bag)

    result = DecompileResult(
        source=source,
        detection=detection,
        pack=pack,
        diagnostics=bag,
        machines=machines,
    )

    if check_roundtrip:
        level = Level.MACHINE if machines else Level.IR
        result.diff = roundtrip(
            source, pack, detection.target, machines=machines or None, level=level
        )
        if not result.diff.identical:
            bag.emit(
                Codes.ROUNDTRIP_MISMATCH,
                result.diff.summary(),
                hint="the decompiled pack does not re-emit identically; "
                "run with --emit ir to inspect what was parsed",
                source=source.label,
            )

    result.output = _render(result, emit)

    bag.emit(
        Codes.STATS,
        f"{len(pack.functions)} function(s), {len(pack.tags)} tag(s), "
        f"{len(machines)} machine(s) from {source.label} for {detection.target} "
        f"(detection: {detection.confidence.value})",
        severity=Severity.INFO,
    )

    if strict:
        result.diagnostics = bag.promoted()

    if dry_run or output is None:
        return result
    if result.diagnostics.has_errors and not force:
        return result

    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(result.output, encoding="utf-8")
    result.output_path = destination
    return result


def _render(result: DecompileResult, emit: str) -> str:
    """Render the requested level, falling back to the IR when lifting failed."""
    if emit == "ir" or not result.machines:
        return render_ir(result.pack, result.detection)
    if emit == "machine":
        return _render_machines(result.machines)
    return generate_python(
        result.machines,
        namespace=result.pack.namespace,
        description=result.pack.description,
        version=result.target.version,
        flavor=result.target.flavor.value,
        origin=result.source.label,
    )


def _render_machines(machines: list[Machine[Any]]) -> str:
    """A readable summary of the reconstructed machines — what ``--emit machine`` prints."""
    lines: list[str] = []
    for machine in machines:
        lines.append(f"machine {machine.name} (initial: {machine.initial})")
        for name, state in machine.states.items():
            marker = " [final]" if state.is_final else ""
            lines.append(f"  state {name}{marker}")
            for phase, commands in (
                ("enter", state.enter),
                ("exit", state.exit),
                ("cycle", state.cycle),
            ):
                for command in commands:
                    lines.append(f"    {phase:<6} {command.name} {dict(command.payload)}")
        for transition in machine.transitions:
            guard = ""
            if transition.condition is not None:
                payload = transition.condition.payload
                guard = (
                    f" when {payload['entry']}.{payload['objective']} "
                    f"== {payload['value']}"
                )
            lines.append(
                f"  {transition.source} --{transition.event}--> "
                f"{transition.target}{guard}"
            )
            for command in transition.commands:
                lines.append(f"    do     {command.name} {dict(command.payload)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
