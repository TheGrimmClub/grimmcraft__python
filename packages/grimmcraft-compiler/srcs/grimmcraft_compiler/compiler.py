"""The compiler pipeline: collect → build IR → validate → render → emit → verify."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from grimmclub import yes
from grimmcraft_compiler.diagnostics import Codes, DiagnosticBag, Severity
from grimmcraft_compiler.emit import emit
from grimmcraft_compiler.ir import Datapack, Resource, ResourceLocation
from grimmcraft_compiler.lower import lower
from grimmcraft_compiler.target import Target
from grimmcraft_compiler.validate import validate_ir, validate_machines
from grimmcraft_compiler.verify import verify_output
from grimmcraft_control.machine import Machine


@dataclass(slots=True)
class CompileResult:
    """The outcome of a compile: the IR, all diagnostics, and the output path."""

    target: Target
    pack: Datapack
    diagnostics: DiagnosticBag
    output_path: Path | None = field(default=None)
    emitted: bool = False

    @property
    def ok(self) -> bool:
        """True when no errors were recorded."""
        return not self.diagnostics.has_errors

    def rendered(self) -> dict[str, str]:
        """Every function's ``ns:path`` id → its rendered ``mcfunction`` text.

        A convenience for inspecting/printing the output (e.g. in examples)
        without reaching for the ``Dialect`` / ``emit`` internals.
        """
        from grimmcraft_compiler.dialect import Dialect
        from grimmcraft_compiler.emit import render_function

        dialect = Dialect(self.target)
        return {str(fn.id): render_function(fn, dialect) for fn in self.pack.functions}


def compile_machines(
    machines: list[Machine[Any]],
    target: Target,
    *,
    namespace: str = "grimmcraft",
    output: Path | None = None,
    zip_output: bool = False,
    strict: bool = False,
    force: bool = False,
    dry_run: bool = False,
    description: str | None = None,
    resources: list[Resource] | None = None,
    DEBUG: bool = yes,
) -> CompileResult:
    """Compile ``machines`` for ``target`` into a datapack.

    Runs the full pipeline and collects diagnostics.  Emission is skipped when
    ``dry_run`` is set, or when errors exist and ``force`` is not; ``strict``
    promotes warnings to errors.  ``resources`` are extra JSON documents to ship
    in the pack (e.g. the ``dialog`` screens a dialogue compiles to).  The
    returned :class:`CompileResult` always carries the IR and diagnostics, plus
    the output path when a pack was written.

    DEBUG: activates debug mode, printing target info and diagnostics on failure.
    """
    bag = DiagnosticBag()
    description = description or f"{namespace} — grimmcraft datapack for {target}"

    # 1-2. Collect + build the dialect-independent IR.
    pack = lower(machines, namespace, description=description)

    # JSON resources a caller generated alongside the machines (dialog screens,
    # loot tables, …). Lowering does not produce these — they come from domain
    # layers built on top of it, such as grimmcraft-npc's dialogue backend.
    if resources:
        pack.resources.extend(resources)

    # Validate the user-supplied namespace up front (helpful, specific source).
    ns_reason = ResourceLocation(namespace, "x").invalid_reason()
    if ns_reason is not None:
        bag.emit(
            Codes.INVALID_RESOURCE_LOCATION,
            f"invalid namespace '{namespace}': {ns_reason}",
            hint="namespaces may contain only [a-z0-9_.-]",
            source="--namespace",
        )

    # 3. Validate against grimmcraft-data + the IR.
    validate_machines(machines, target, bag)
    validate_ir(pack, bag)

    # --strict: promote warnings to errors for the gate and the report.
    if strict:
        bag = bag.promoted()

    bag.emit(
        Codes.STATS,
        f"{len(machines)} machine(s), {len(pack.functions)} function(s), "
        f"{len(pack.tags)} tag(s) for {target}",
        severity=Severity.INFO,
    )

    result = CompileResult(target=target, pack=pack, diagnostics=bag)

    # 5-6. Emit unless dry-run or blocked by errors.
    if dry_run:
        return result
    if bag.has_errors and not force:
        return result

    out = Path(output) if output is not None else Path(f"dist/{namespace}")
    path = emit(pack, target, out, zip_output=zip_output)
    result.output_path = path
    result.emitted = True

    # 7. Verify the emitted tree (verify the directory even when zipped).
    verify_root = out if zip_output else path
    verify_output(verify_root, target, bag)

    if DEBUG:
        print(f"target    : {target}")
        print(f"ok        : {result.ok}")
        if result.ok:
            print(f"functions : {len(result.pack.functions)}")
            print(f"output    : {result.output_path}")
        else:
            print(f"error:    : {result.diagnostics}")

    return result


def show_info(
    target: Target,
    DEBUG: bool = yes,
) -> None:
    """Outputs the information for the target to the console.

    DEBUG: activates debug mode, printing target info and diagnostics on failure.
    """
    info = target.info
    folder = "function" if info.singular_folders else "functions"
    data_model = "components" if info.uses_components else "NBT tags"
    print(f"\n=== {target} ===")
    print(f"  pack format : {info.format_label}")
    print(f"  folders     : data/<ns>/{folder}/…")
    print(f"  item data   : {data_model}")
