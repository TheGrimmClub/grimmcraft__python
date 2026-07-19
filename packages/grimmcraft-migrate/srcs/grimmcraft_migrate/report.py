"""The Markdown migration report.

Three audiences, three sections: what changed (so it can be reviewed), what was
preserved under ``custom_data`` (so nothing is assumed lost), and what was left
alone and why (so failures are visible rather than silent).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from grimmcraft_migrate.inventory import CommandEntry
from grimmcraft_migrate.migrate import MigrationResult


@dataclass
class MigrationReport:
    """Everything the migration did, ready to render as Markdown."""

    results: list[tuple[CommandEntry, MigrationResult]] = field(default_factory=list)

    def add(self, entry: CommandEntry, result: MigrationResult) -> None:
        self.results.append((entry, result))

    # --- summary numbers -----------------------------------------------------
    @property
    def changed(self) -> list[tuple[CommandEntry, MigrationResult]]:
        return [pair for pair in self.results if pair[1].changed]

    @property
    def failed(self) -> list[tuple[CommandEntry, MigrationResult]]:
        return [pair for pair in self.results if pair[1].failed]

    @property
    def untouched(self) -> list[tuple[CommandEntry, MigrationResult]]:
        return [
            pair for pair in self.results if not pair[1].changed and not pair[1].failed
        ]

    def rule_frequency(self) -> Counter[str]:
        counts: Counter[str] = Counter()
        for _, result in self.results:
            for transformation in result.transformations:
                counts[transformation.rule] += 1
        return counts

    def unknown_key_frequency(self) -> Counter[str]:
        counts: Counter[str] = Counter()
        for _, result in self.results:
            for key in result.unknown_keys:
                counts[key] += 1
        return counts

    # --- rendering -----------------------------------------------------------
    def to_markdown(self) -> str:
        total = len(self.results)
        lines = [
            "# Command migration report",
            "",
            f"- {total} command(s) processed",
            f"- {len(self.changed)} migrated",
            f"- {len(self.untouched)} already current (unchanged)",
            f"- {len(self.failed)} could not be migrated (left unchanged)",
            "",
        ]

        rules = self.rule_frequency()
        if rules:
            lines += ["## Transformations applied", "", "| count | rule |",
                      "|------:|------|"]
            for rule, count in rules.most_common():
                lines.append(f"| {count} | `{rule}` |")
            lines.append("")

        unknown = self.unknown_key_frequency()
        lines += ["## Unknown keys", ""]
        if not unknown:
            lines += ["None — every legacy key had a mapping.", ""]
        else:
            lines += [
                "These had no mapping and were **preserved** under "
                "`minecraft:custom_data` rather than dropped. Each is worth a "
                "look: the game will keep the data but no longer act on it.",
                "",
                "| count | key |",
                "|------:|-----|",
            ]
            for key, count in unknown.most_common():
                lines.append(f"| {count} | `{key}` |")
            lines.append("")

        if self.failed:
            lines += [
                "## Left unchanged (could not migrate)",
                "",
                "These were **not** rewritten, so the output still holds the "
                "original command. Nothing was half-transformed.",
                "",
            ]
            for entry, result in self.failed:
                lines += [
                    f"### `{entry.location}`",
                    "",
                    f"- reason: {result.unchanged_reason}",
                    "",
                    "```",
                    result.original,
                    "```",
                    "",
                ]

        if self.changed:
            lines += ["## Migrated commands", ""]
            for entry, result in self.changed:
                applied = ", ".join(
                    sorted({t.rule for t in result.transformations})
                ) or "(none)"
                lines += [
                    f"### `{entry.location}`",
                    "",
                    f"- rules: {applied}",
                    "",
                    "```diff",
                    f"- {result.original}",
                    f"+ {result.migrated}",
                    "```",
                    "",
                ]

        return "\n".join(lines).rstrip() + "\n"
