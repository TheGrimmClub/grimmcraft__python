"""The classifier pass — count what is actually there before changing anything.

Run first, on purpose.  A migration written against a *guess* about the corpus
wastes effort on rules nothing uses and misses the one that matters, so this
answers "which transformations does this inventory actually need?" before a
single command is rewritten.

This is the one module where regular expressions are appropriate: it only
*counts* legacy shapes, and a miscount is harmless.  The transformation itself
parses properly, because there a mistake corrupts data.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from grimmcraft_migrate.inventory import Inventory
from grimmcraft_migrate.rules import ATTRIBUTE_RENAMES

#: An item id followed directly by ``{`` — legacy item NBT.
LEGACY_ITEM_NBT = re.compile(r"(?:[a-z0-9_.-]+:)?[a-z0-9_.-]+\{")

#: A sign's legacy per-line fields.
LEGACY_SIGN_FIELDS = re.compile(r"\bText[1-4]\s*:")

#: The legacy nested-item schema — ``Count:`` as a sibling of ``id:``.
LEGACY_ITEM_COUNT = re.compile(r"\bCount\s*:")

#: The legacy ``tag:{`` wrapper inside an item compound.
LEGACY_ITEM_TAG = re.compile(r"\btag\s*:\s*\{")

#: A dotted attribute identifier from a known family.
LEGACY_ATTRIBUTE = re.compile(r"\b(?:generic|horse|zombie|player)\.[a-z_]+\b")

#: ``{X:…,Y:…,Z:…}`` block positions that became integer arrays.
LEGACY_BLOCK_POSITION = re.compile(r"\{\s*X\s*:[^}]*Y\s*:[^}]*Z\s*:[^}]*\}")

#: Every flag the classifier can raise, with the rule that would handle it.
FLAG_DESCRIPTIONS: dict[str, str] = {
    "legacy_item_nbt": "item NBT in brace syntax (needs the component rewrite)",
    "legacy_sign_fields": "Text1..Text4 sign lines (needs front_text.messages)",
    "legacy_item_count": "nested items using Count (needs count/components)",
    "legacy_item_tag": "nested items using tag (needs count/components)",
    "legacy_attribute": "dotted attribute names (needs the rename table)",
    "legacy_block_position": "{X,Y,Z} positions (needs [I;x,y,z])",
}


@dataclass
class ClassificationReport:
    """What the inventory contains, and which rules it will need."""

    total_commands: int = 0
    command_frequency: Counter[str] = field(default_factory=Counter)
    flag_frequency: Counter[str] = field(default_factory=Counter)
    #: Flag → a few example commands, so a reviewer can eyeball each rule.
    examples: dict[str, list[str]] = field(default_factory=dict)

    @property
    def needed_flags(self) -> list[str]:
        """Every flag that actually occurred, most frequent first."""
        return [flag for flag, _ in self.flag_frequency.most_common()]

    def to_markdown(self) -> str:
        """The report as Markdown."""
        lines = [
            "# Command inventory classification",
            "",
            f"{self.total_commands} command(s) scanned.",
            "",
            "## Commands by name",
            "",
            "| count | command |",
            "|------:|---------|",
        ]
        for name, count in self.command_frequency.most_common():
            lines.append(f"| {count} | `{name}` |")

        lines += ["", "## Legacy syntax found", ""]
        if not self.flag_frequency:
            lines.append("None — this inventory appears to be 1.21 syntax already.")
        else:
            lines += ["| count | what | rule needed |", "|------:|------|-------------|"]
            for flag, count in self.flag_frequency.most_common():
                lines.append(
                    f"| {count} | `{flag}` | {FLAG_DESCRIPTIONS.get(flag, '')} |"
                )
            lines += ["", "### Examples", ""]
            for flag in self.needed_flags:
                lines.append(f"**`{flag}`**")
                lines.append("")
                for example in self.examples.get(flag, []):
                    lines.append(f"```\n{example}\n```")
                lines.append("")
        return "\n".join(lines).rstrip() + "\n"


def command_name(command: str) -> str:
    """The leading verb of a command, ``execute … run <verb>`` included.

    Grouping ``execute`` by its *inner* command is what makes the frequency
    table useful — otherwise half a corpus is simply "execute".
    """
    text = command.strip().lstrip("/")
    if not text:
        return "(empty)"
    verb = text.split(" ", 1)[0]
    if verb == "execute" and " run " in text:
        inner = text.split(" run ", 1)[1].strip()
        if inner:
            return f"execute→{inner.split(' ', 1)[0]}"
    return verb


def classify_command(command: str) -> list[str]:
    """Every legacy-syntax flag raised by one command."""
    flags: list[str] = []
    if LEGACY_ITEM_NBT.search(command):
        flags.append("legacy_item_nbt")
    if LEGACY_SIGN_FIELDS.search(command):
        flags.append("legacy_sign_fields")
    if LEGACY_ITEM_COUNT.search(command):
        flags.append("legacy_item_count")
    if LEGACY_ITEM_TAG.search(command):
        flags.append("legacy_item_tag")
    match = LEGACY_ATTRIBUTE.search(command)
    if match is not None and match.group(0) in ATTRIBUTE_RENAMES:
        flags.append("legacy_attribute")
    if LEGACY_BLOCK_POSITION.search(command):
        flags.append("legacy_block_position")
    return flags


def classify_inventory(
    inventory: Inventory, *, examples_per_flag: int = 3
) -> ClassificationReport:
    """Scan an inventory and report what is in it."""
    report = ClassificationReport(total_commands=len(inventory))
    for entry in inventory:
        report.command_frequency[command_name(entry.command)] += 1
        for flag in classify_command(entry.command):
            report.flag_frequency[flag] += 1
            shown = report.examples.setdefault(flag, [])
            if len(shown) < examples_per_flag:
                shown.append(entry.command)
    return report
