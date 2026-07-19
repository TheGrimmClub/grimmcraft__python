#!/usr/bin/env python3
"""Per-package statistics for the workspace: size, shape, tests and docs.

Counts by parsing each file with :mod:`ast` rather than by matching text, so a
``def`` inside a docstring or a string containing ``class `` cannot inflate the
numbers.  Lines are attributed to exactly one of four buckets — code, docstring,
comment, blank — which is what makes "how much of this is documentation?" a
question with an answer.

Run it through the Taskfile::

    task statistics                 # the table
    task statistics -- --facts      # plus derived observations
    task statistics -- --csv        # machine-readable

Standard library only *by default*, so it still runs on a fresh clone with no
environment at all. Two optional upgrades are used when they happen to be
importable, and silently skipped when they are not:

- **rich** colours the numbers against the thresholds;
- **PyYAML** reads those thresholds from ``statistics.yaml``.

Without them the table is plain and the built-in thresholds apply, so the tool
never fails because of what is missing — it just says less. ``task statistics``
runs it through ``uv`` so both are present.
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
import sys
from dataclasses import dataclass, field
from pathlib import Path

#: Directories that are never part of a package's own source.
IGNORED_DIRECTORY_NAMES = frozenset(
    {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "dist", "build"}
)

#: Test *data* that happens to contain Python — generator scripts shipped inside
#: datapack fixtures. Counting them would say this repo is mostly other people's
#: code, which is true of the directory and false of the project.
IGNORED_PATH_FRAGMENTS = ("/datapacks/",)


#: Used when statistics.yaml cannot be read (no PyYAML, or no file). Kept in
#: step with the shipped statistics.yaml, which is the editable copy.
BUILT_IN_RULES: dict[str, dict[str, object]] = {
    "doc%": {"higher_is_better": True, "green": 80, "yellow": 60},
    "test/code": {"higher_is_better": True, "green": 0.5, "yellow": 0.2},
    "code/file": {"higher_is_better": False, "green": 150, "yellow": 300},
}


#: Used when no groups are configured: one section, everything in it.
BUILT_IN_GROUPS: list[dict[str, object]] = [{"name": "all packages", "match": ["*"]}]


@dataclass
class Configuration:
    """What statistics.yaml says, or the built-in defaults when it says nothing."""

    rules: dict[str, dict[str, object]] = field(default_factory=lambda: BUILT_IN_RULES)
    exemptions: dict[str, dict[str, str]] = field(default_factory=dict)
    groups: list[dict[str, object]] = field(default_factory=lambda: BUILT_IN_GROUPS)


def load_configuration(root: Path) -> Configuration:
    """Read ``statistics.yaml``, falling back to the built-in defaults.

    A missing file or a missing PyYAML is not an error: the tool is meant to run
    anywhere, and thresholds it cannot read are thresholds it does without.
    """
    configuration_file = root / "statistics.yaml"
    try:
        import yaml
    except ModuleNotFoundError:
        return Configuration()
    if not configuration_file.exists():
        return Configuration()
    document = yaml.safe_load(configuration_file.read_text(encoding="utf-8")) or {}
    return Configuration(
        rules=document.get("rules", BUILT_IN_RULES),
        exemptions=document.get("exemptions", {}),
        groups=document.get("groups", BUILT_IN_GROUPS),
    )


def group_packages(
    packages: list[PackageStatistics], groups: list[dict[str, object]]
) -> list[tuple[str, list[PackageStatistics]]]:
    """Gather packages into their configured sections, in configured order.

    A package joins the first group that matches it, so a broad pattern can sit
    after narrow ones and act as the catch-all for its family. Anything matched
    by nothing is returned under "ungrouped" rather than dropped — a package
    left out of the configuration should be visible, not invisible.
    """
    from fnmatch import fnmatch

    remaining = list(packages)
    sections: list[tuple[str, list[PackageStatistics]]] = []
    for group in groups:
        patterns = [str(pattern) for pattern in group.get("match", [])]  # type: ignore[union-attr]
        members = [
            package
            for package in remaining
            if any(fnmatch(package.name, pattern) for pattern in patterns)
        ]
        if members:
            sections.append((str(group.get("name", "?")), members))
            remaining = [package for package in remaining if package not in members]
    if remaining:
        sections.append(("ungrouped", remaining))
    return sections


def grade(value: float, rule: dict[str, object]) -> str:
    """``"green"``, ``"yellow"`` or ``"red"`` for ``value`` under ``rule``."""
    green, yellow = float(rule["green"]), float(rule["yellow"])  # type: ignore[arg-type]
    if rule.get("higher_is_better", True):
        if value >= green:
            return "green"
        return "yellow" if value >= yellow else "red"
    if value <= green:
        return "green"
    return "yellow" if value <= yellow else "red"


@dataclass
class SourceMetrics:
    """What one set of Python files contains."""

    code_lines: int = 0
    docstring_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    documented_definitions: int = 0
    total_definitions: int = 0
    file_count: int = 0

    @property
    def lines_per_file(self) -> int:
        """Average lines of code per source file, 0 when there are none."""
        if not self.file_count:
            return 0
        return round(self.code_lines / self.file_count)

    @property
    def documentation_coverage_percent(self) -> int:
        """Share of modules, classes and functions carrying a docstring."""
        if not self.total_definitions:
            return 0
        return round(100 * self.documented_definitions / self.total_definitions)

    @property
    def total_lines(self) -> int:
        return (
            self.code_lines
            + self.docstring_lines
            + self.comment_lines
            + self.blank_lines
        )


@dataclass
class PackageStatistics:
    """Everything measured about one package."""

    name: str
    source: SourceMetrics = field(default_factory=SourceMetrics)
    tests: SourceMetrics = field(default_factory=SourceMetrics)
    test_function_count: int = 0
    markdown_file_count: int = 0
    markdown_line_count: int = 0
    file_count: int = 0
    directory_count: int = 0

    @property
    def test_to_code_ratio(self) -> float:
        """Test code lines per line of source code."""
        if not self.source.code_lines:
            return 0.0
        return self.tests.code_lines / self.source.code_lines


def _is_ignored(path: Path) -> bool:
    if any(part in IGNORED_DIRECTORY_NAMES for part in path.parts):
        return True
    posix = path.as_posix()
    return any(fragment in posix for fragment in IGNORED_PATH_FRAGMENTS)


def _python_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return [path for path in sorted(directory.rglob("*.py")) if not _is_ignored(path)]


def _docstring_line_numbers(tree: ast.AST) -> set[int]:
    """Every line occupied by a docstring, so it is not counted as code."""
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        if not node.body:
            continue
        first = node.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            end = first.value.end_lineno or first.value.lineno
            lines.update(range(first.value.lineno, end + 1))
    return lines


def measure(files: list[Path]) -> SourceMetrics:
    """Measure a set of Python files."""
    metrics = SourceMetrics(file_count=len(files))

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        try:
            tree: ast.AST | None = ast.parse(text)
        except SyntaxError:
            tree = None  # still worth counting its lines

        docstring_lines: set[int] = set()
        if tree is not None:
            docstring_lines = _docstring_line_numbers(tree)
            metrics.total_definitions += 1  # the module itself
            if ast.get_docstring(tree):  # type: ignore[arg-type]
                metrics.documented_definitions += 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    metrics.function_count += 1
                elif isinstance(node, ast.ClassDef):
                    metrics.class_count += 1
                else:
                    continue
                metrics.total_definitions += 1
                if ast.get_docstring(node):
                    metrics.documented_definitions += 1

        for number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if number in docstring_lines:
                metrics.docstring_lines += 1
            elif not stripped:
                metrics.blank_lines += 1
            elif stripped.startswith("#"):
                metrics.comment_lines += 1
            else:
                metrics.code_lines += 1

    return metrics


def count_test_functions(files: list[Path]) -> int:
    """Test *functions* — not the parametrised cases pytest expands them into."""
    total = 0
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and node.name.startswith("test"):
                total += 1
    return total


def analyse_package(package_directory: Path) -> PackageStatistics:
    """Measure one package directory."""
    statistics = PackageStatistics(name=package_directory.name)

    statistics.source = measure(_python_files(package_directory / "srcs"))
    test_files = _python_files(package_directory / "tests")
    statistics.tests = measure(test_files)
    statistics.test_function_count = count_test_functions(test_files)

    markdown_files = [
        path
        for path in sorted(package_directory.rglob("*.md"))
        if not _is_ignored(path)
    ]
    statistics.markdown_file_count = len(markdown_files)
    for path in markdown_files:
        try:
            statistics.markdown_line_count += len(
                path.read_text(encoding="utf-8").splitlines()
            )
        except (OSError, UnicodeDecodeError):
            continue

    statistics.file_count = sum(
        1 for path in package_directory.rglob("*") if path.is_file() and not _is_ignored(path)
    )
    statistics.directory_count = sum(
        1 for path in package_directory.rglob("*") if path.is_dir() and not _is_ignored(path)
    )
    return statistics


def analyse_workspace(packages_directory: Path) -> list[PackageStatistics]:
    """Measure every package, alphabetically."""
    return [
        analyse_package(directory)
        for directory in sorted(packages_directory.iterdir())
        if directory.is_dir() and not _is_ignored(directory)
    ]


COLUMNS: list[tuple[str, int]] = [
    ("package", 24),
    ("code", 7),
    ("docstr", 7),
    ("fn", 5),
    ("cls", 5),
    ("doc%", 6),
    ("test/code", 10),
    ("code/file", 10),
    ("srcF", 6),
    ("tests", 7),
    ("testC", 7),
    ("md", 4),
    ("mdLn", 6),
    ("files", 6),
    ("dirs", 5),
]


def _row(statistics: PackageStatistics) -> list[str]:
    return [
        statistics.name,
        str(statistics.source.code_lines),
        str(statistics.source.docstring_lines),
        str(statistics.source.function_count),
        str(statistics.source.class_count),
        f"{statistics.source.documentation_coverage_percent}%",
        f"{statistics.test_to_code_ratio:.2f}",
        str(statistics.source.lines_per_file),
        str(statistics.source.file_count),
        str(statistics.test_function_count),
        str(statistics.tests.code_lines),
        str(statistics.markdown_file_count),
        str(statistics.markdown_line_count),
        str(statistics.file_count),
        str(statistics.directory_count),
    ]


def totals(packages: list[PackageStatistics]) -> PackageStatistics:
    """The whole workspace as one row.

    Note the derived columns are recomputed from the summed lines rather than
    averaged across packages: the mean of twelve ratios is not the ratio of the
    workspace, and the difference is large when the packages differ in size.
    """
    total = PackageStatistics(name="TOTAL")
    for statistics in packages:
        total.source.code_lines += statistics.source.code_lines
        total.source.docstring_lines += statistics.source.docstring_lines
        total.source.function_count += statistics.source.function_count
        total.source.class_count += statistics.source.class_count
        total.source.file_count += statistics.source.file_count
        total.tests.code_lines += statistics.tests.code_lines
        total.test_function_count += statistics.test_function_count
        total.markdown_file_count += statistics.markdown_file_count
        total.markdown_line_count += statistics.markdown_line_count
        total.file_count += statistics.file_count
        total.directory_count += statistics.directory_count
    return total


#: Which column each rule grades, by column name.
GRADED_COLUMNS = ("doc%", "test/code", "code/file")


def _numeric(value: str) -> float:
    """The number inside a rendered cell (``"82%"`` -> ``82.0``)."""
    return float(value.rstrip("%"))


def render_rich_table(packages: list[PackageStatistics], configuration: Configuration) -> bool:
    """Print the table in colour, grouped by family. False when rich is absent.

    Exempt cells are dimmed rather than coloured: an exemption is a decision
    someone made, so it should look different from a number nobody graded.
    """
    try:
        from rich import box
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
    except ModuleNotFoundError:
        return False

    table = Table(box=box.SIMPLE_HEAVY, pad_edge=False, header_style="bold")
    for index, (name, _width) in enumerate(COLUMNS):
        table.add_column(name, justify="left" if index == 0 else "right")

    def cells_for(statistics: PackageStatistics) -> list[str]:
        rendered = []
        for value, (name, _width) in zip(_row(statistics), COLUMNS, strict=True):
            rule = configuration.rules.get(name)
            exempt = configuration.exemptions.get(statistics.name, {}).get(name)
            if exempt:
                rendered.append(f"[dim]{value}[/]")
            elif name in GRADED_COLUMNS and rule is not None:
                rendered.append(f"[{grade(_numeric(value), rule)}]{value}[/]")
            else:
                rendered.append(value)
        return rendered

    for section_name, members in group_packages(packages, configuration.groups):
        for statistics in members:
            table.add_row(*cells_for(statistics))

        subtotal = _row(totals(members))
        subtotal[0] = f"{section_name}  ({len(members)})"
        subtotal[5] = ""  # a coverage average across packages would mean nothing
        table.add_row(*(f"[bold cyan]{value}[/]" for value in subtotal))
        table.add_section()

    grand = _row(totals(packages))
    grand[5] = ""
    table.add_row(*(f"[bold]{value}[/]" for value in grand))

    console = Console()
    console.print(table)

    graded_columns = [name for name in GRADED_COLUMNS if name in configuration.rules]
    legend = [
        "[bold]code[/] executable lines only — docstrings, comments and blanks excluded",
        "[bold]doc%[/] definitions carrying a docstring",
        "[bold]test/code[/] lines of test per line of source",
        "[bold]tests[/] test functions, before pytest expands parametrised cases",
        "",
        f"graded against statistics.yaml: {', '.join(graded_columns)}",
    ]
    if configuration.exemptions:
        legend.append("")
        legend.append("[dim]dimmed cells are exempt, each for a stated reason:[/]")
        for package, columns in configuration.exemptions.items():
            for column, reason in columns.items():
                legend.append(f"[dim]  {package} · {column} — {reason.strip()}[/]")
    console.print(Panel("\n".join(legend), title="legend", title_align="left", box=box.ROUNDED))
    return True


def render_table(packages: list[PackageStatistics]) -> str:
    """The human-readable table."""
    lines = ["".join(name.ljust(width) for name, width in COLUMNS)]
    lines.append("─" * sum(width for _, width in COLUMNS))

    for statistics in packages:
        lines.append(
            "".join(
                value.ljust(width)
                for value, (_, width) in zip(_row(statistics), COLUMNS, strict=True)
            )
        )

    total = totals(packages)
    lines.append("─" * sum(width for _, width in COLUMNS))
    row = _row(total)
    row[5] = ""  # a coverage average across packages would be meaningless
    lines.append(
        "".join(
            value.ljust(width) for value, (_, width) in zip(row, COLUMNS, strict=True)
        )
    )
    lines.append("")
    lines.append(
        "code = executable lines (docstrings, comments and blanks excluded) · "
        "doc% = definitions with a docstring"
    )
    lines.append(
        "tests = test functions, before pytest expands parametrised cases"
    )
    return "\n".join(lines)


def render_facts(packages: list[PackageStatistics]) -> str:
    """Derived observations — the things the raw table implies but does not say."""
    lines = ["", "Observations", "─" * 12]

    by_code = sorted(packages, key=lambda p: p.source.code_lines, reverse=True)
    total_code = sum(p.source.code_lines for p in packages)
    largest = by_code[0]
    share = round(100 * largest.source.code_lines / total_code) if total_code else 0
    lines.append(
        f"· {largest.name} is {share}% of all code "
        f"({largest.source.code_lines} of {total_code} lines)."
    )

    total_docstrings = sum(p.source.docstring_lines for p in packages)
    total_markdown = sum(p.markdown_line_count for p in packages)
    lines.append(
        f"· Documentation is {total_docstrings} docstring lines + "
        f"{total_markdown} Markdown lines against {total_code} code lines "
        f"(~{round(100 * (total_docstrings + total_markdown) / total_code)}% as much)."
    )

    tested = [p for p in packages if p.source.code_lines and p.tests.code_lines]
    if tested:
        best = max(tested, key=lambda p: p.test_to_code_ratio)
        worst = min(tested, key=lambda p: p.test_to_code_ratio)
        lines.append(
            f"· Test-to-code ratio spans {worst.test_to_code_ratio:.2f} "
            f"({worst.name}) to {best.test_to_code_ratio:.2f} ({best.name})."
        )

    documented = [p for p in packages if p.source.total_definitions]
    if documented:
        best_doc = max(documented, key=lambda p: p.source.documentation_coverage_percent)
        lines.append(
            f"· Best-documented package: {best_doc.name} at "
            f"{best_doc.source.documentation_coverage_percent}%."
        )

    heaviest = max(packages, key=lambda p: p.file_count)
    lines.append(
        f"· Most files: {heaviest.name} with {heaviest.file_count} — "
        "check whether that is source or fixtures."
    )
    return "\n".join(lines)


def render_csv(packages: list[PackageStatistics]) -> str:
    """Machine-readable output, for tracking these over time."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([name for name, _ in COLUMNS])
    for statistics in packages:
        writer.writerow(_row(statistics))
    return buffer.getvalue().rstrip("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="statistics", description="Per-package statistics for the workspace."
    )
    parser.add_argument(
        "--packages-directory",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "packages",
        help="where the packages live (default: ../packages)",
    )
    parser.add_argument(
        "--facts", action="store_true", help="also print derived observations"
    )
    parser.add_argument("--csv", action="store_true", help="emit CSV instead of a table")
    arguments = parser.parse_args(argv)

    if not arguments.packages_directory.is_dir():
        print(f"no packages directory at {arguments.packages_directory}", file=sys.stderr)
        return 2

    packages = analyse_workspace(arguments.packages_directory)
    if arguments.csv:
        print(render_csv(packages))
        return 0

    configuration = load_configuration(arguments.packages_directory.parent)
    if not render_rich_table(packages, configuration):
        print(render_table(packages))
    if arguments.facts:
        print(render_facts(packages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
