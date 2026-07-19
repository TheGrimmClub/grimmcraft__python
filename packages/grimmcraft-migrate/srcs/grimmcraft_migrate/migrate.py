"""The transformation: one 1.19 command string in, one 1.21 command string out.

Every rewrite is recorded, and a command that cannot be parsed is returned
**unchanged** with the reason attached — never half-transformed, because a
partially rewritten command is worse than an untouched one: it looks migrated.

Idempotency is structural rather than checked after the fact. Each pass asks
"is this the *legacy* shape?" before doing anything — legacy item NBT is a brace
directly after an item id, a legacy sign has ``Text1``, a legacy attribute name
contains a dot. Modern input matches none of those, so a second run changes
nothing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from grimmcraft_migrate.rules import (
    ATTRIBUTE_RENAMES,
    BLOCK_POSITION_FIELDS,
    COMPONENT_RULES,
    CUSTOM_DATA_COMPONENT,
    DISPLAY_KEYS,
    ITEM_CONTAINER_KEYS,
)
from grimmcraft_migrate.snbt import (
    SnbtCompound,
    SnbtList,
    SnbtNumber,
    SnbtString,
    SnbtSyntaxError,
    SnbtValue,
    find_matching_brace,
    parse_compound,
)

#: Commands whose arguments carry item data in the ``item{…}`` position.
ITEM_ARGUMENT_COMMANDS = ("give", "clear", "item", "loot", "replaceitem")

#: Commands carrying entity / block-entity NBT compounds.
NBT_ARGUMENT_COMMANDS = ("summon", "setblock", "fill", "data")


def effective_verb(command: str) -> str:
    """The command that actually runs — following ``execute … run`` to its tail.

    Resolving this matters twice over: ``execute … run give`` must get the item
    rewrite, and ``execute … run say {`` must *not* be treated as malformed NBT
    just because it contains a brace.
    """
    text = command.strip().lstrip("/")
    verb = text.split(" ", 1)[0]
    while verb == "execute" and " run " in text:
        text = text.split(" run ", 1)[1].strip()
        verb = text.split(" ", 1)[0]
    return verb

#: An item identifier immediately followed by ``{`` — the legacy item NBT shape.
LEGACY_ITEM_PATTERN = re.compile(
    r"(?P<identifier>(?:[a-z0-9_.-]+:)?[a-z0-9_.-]+)(?P<brace>\{)"
)

#: A legacy attribute name: a dotted identifier in a known family.
LEGACY_ATTRIBUTE_PATTERN = re.compile(
    r"\b(generic|horse|zombie|player)\.[a-z_]+\b"
)


@dataclass
class Transformation:
    """One change applied to one command, for the report."""

    rule: str
    detail: str


@dataclass
class MigrationResult:
    """The outcome for a single command."""

    original: str
    migrated: str
    transformations: list[Transformation] = field(default_factory=list)
    #: Legacy keys with no mapping, preserved under ``custom_data``.
    unknown_keys: list[str] = field(default_factory=list)
    #: Set when the command was left alone, explaining why.
    unchanged_reason: str = ""

    @property
    def changed(self) -> bool:
        return self.original != self.migrated

    @property
    def failed(self) -> bool:
        return bool(self.unchanged_reason)


class CommandMigrator:
    """Migrates command strings from 1.19 syntax to 1.21 syntax."""

    def __init__(self) -> None:
        self.transformations: list[Transformation] = []
        self.unknown_keys: list[str] = []

    # --- entry point ---------------------------------------------------------
    def migrate_command(self, command: str) -> MigrationResult:
        """Migrate one command, never raising."""
        self.transformations = []
        self.unknown_keys = []
        try:
            migrated = self._migrate(command)
        except SnbtSyntaxError as error:
            return MigrationResult(
                original=command,
                migrated=command,
                unchanged_reason=f"could not parse the command's NBT: {error}",
            )
        except (ValueError, KeyError, IndexError) as error:
            return MigrationResult(
                original=command,
                migrated=command,
                unchanged_reason=f"unexpected problem while migrating: {error}",
            )
        return MigrationResult(
            original=command,
            migrated=migrated,
            transformations=list(self.transformations),
            unknown_keys=list(self.unknown_keys),
        )

    def _migrate(self, command: str) -> str:
        text = self._migrate_attribute_names(command)
        text = self._migrate_item_arguments(text)
        text = self._migrate_embedded_compounds(text)
        return text

    # --- 4. attribute renames ------------------------------------------------
    def _migrate_attribute_names(self, command: str) -> str:
        """Rename ``generic.movement_speed`` → ``minecraft:movement_speed``."""

        def replace(match: re.Match[str]) -> str:
            legacy = match.group(0)
            modern = ATTRIBUTE_RENAMES.get(legacy)
            if modern is None:
                return legacy
            self.transformations.append(
                Transformation("attribute_rename", f"{legacy} → {modern}")
            )
            return modern

        return LEGACY_ATTRIBUTE_PATTERN.sub(replace, command)

    # --- 1. item NBT → components -------------------------------------------
    def _migrate_item_arguments(self, command: str) -> str:
        """Rewrite ``item{…}`` into ``item[…]`` for item-bearing commands.

        Only the *first* token of the command decides whether item arguments are
        possible, so a ``say`` mentioning braces is left alone.
        """
        if effective_verb(command) not in ITEM_ARGUMENT_COMMANDS:
            return command

        result = command
        position = 0
        while True:
            match = LEGACY_ITEM_PATTERN.search(result, position)
            if match is None:
                return result
            brace_start = match.start("brace")
            # Only an item id followed directly by '{' — and the identifier must
            # not itself be a key inside a compound (which ':' would indicate).
            identifier_start = match.start("identifier")
            preceding = result[identifier_start - 1 : identifier_start]
            if identifier_start > 0 and preceding in (":", '"'):
                position = brace_start + 1
                continue
            # An unbalanced brace inside an item-bearing command is a genuine
            # error, not "this isn't item data" — let it propagate so the
            # command is reported and left whole rather than half-rewritten.
            end = find_matching_brace(result, brace_start)

            raw = result[brace_start:end]
            compound = parse_compound(raw)
            components = self._compound_to_components(compound)
            if components is None:
                position = end
                continue

            self.transformations.append(
                Transformation(
                    "item_nbt_to_components",
                    f"{match.group('identifier')}{raw} → "
                    f"{match.group('identifier')}{components}",
                )
            )
            result = result[:brace_start] + components + result[end:]
            position = brace_start + len(components)

    def _compound_to_components(self, compound: SnbtCompound) -> str | None:
        """Render a legacy item tag as a ``[component=value,…]`` list."""
        components: dict[str, SnbtValue] = {}
        leftovers = SnbtCompound()

        for key, value in list(compound.items()):
            if key == "display" and isinstance(value, SnbtCompound):
                self._migrate_display(value, components, leftovers)
                continue
            rule = COMPONENT_RULES.get(key)
            if rule is None:
                leftovers[key] = value
                self.unknown_keys.append(key)
                continue
            transformed = rule.transform(value)
            self._merge_component(components, rule.component, transformed)
            if rule.approximate:
                self.transformations.append(
                    Transformation("approximate", f"{key}: {rule.note}")
                )

        if leftovers.entries:
            components[CUSTOM_DATA_COMPONENT] = leftovers
        if not components:
            return None
        body = ",".join(
            f"{name}={value.to_snbt()}" for name, value in components.items()
        )
        return f"[{body}]"

    def _migrate_display(
        self,
        display: SnbtCompound,
        components: dict[str, SnbtValue],
        leftovers: SnbtCompound,
    ) -> None:
        """``display.Name`` / ``.Lore`` / ``.color`` each became a component."""
        remaining = SnbtCompound()
        for key, value in display.items():
            if key not in DISPLAY_KEYS:
                remaining[key] = value
                self.unknown_keys.append(f"display.{key}")
                continue
            rule = COMPONENT_RULES[f"display.{key}"]
            self._merge_component(components, rule.component, rule.transform(value))
        if remaining.entries:
            leftovers["display"] = remaining

    @staticmethod
    def _merge_component(
        components: dict[str, SnbtValue], name: str, value: SnbtValue
    ) -> None:
        """Add a component, merging when two legacy keys map to the same one.

        ``Potion`` and ``CustomPotionEffects`` both become ``potion_contents``,
        and ``pages``/``title``/``author`` all become ``written_book_content``.
        """
        existing = components.get(name)
        if isinstance(existing, SnbtCompound) and isinstance(value, SnbtCompound):
            existing.entries.update(value.entries)
            return
        components[name] = value

    # --- 2, 3, 6. nested NBT in summon / setblock / fill / data merge --------
    def _migrate_embedded_compounds(self, command: str) -> str:
        """Rewrite entity/block-entity NBT: nested items, signs, block positions."""
        if effective_verb(command) not in NBT_ARGUMENT_COMMANDS:
            return command

        brace = command.find("{")
        if brace == -1:
            return command
        end = find_matching_brace(command, brace)

        compound = parse_compound(command[brace:end])
        changed = self._rewrite_nested(compound)
        if not changed:
            return command
        return command[:brace] + compound.to_snbt() + command[end:]

    def _rewrite_nested(self, value: SnbtValue) -> bool:
        """Walk a compound, applying the nested-NBT migrations. Returns changed."""
        changed = False
        if isinstance(value, SnbtList):
            for item in value.items:
                changed |= self._rewrite_nested(item)
            return changed
        if not isinstance(value, SnbtCompound):
            return False

        # 3. signs: Text1..Text4 → front_text.messages
        if any(f"Text{index}" in value for index in (1, 2, 3, 4)):
            messages = SnbtList()
            for index in (1, 2, 3, 4):
                line = value.pop(f"Text{index}")
                # A sign always has four lines, so absent ones become empty
                # components — single-quoted like the JSON strings beside them,
                # which avoids escaping the quotes inside.
                messages.items.append(
                    line
                    if isinstance(line, SnbtString)
                    else SnbtString('{"text":""}', "'")
                )
            front = SnbtCompound()
            front["messages"] = messages
            value["front_text"] = front
            self.transformations.append(
                Transformation("sign_text", "Text1..Text4 → front_text.messages")
            )
            changed = True

        # 6. block positions: {X:1,Y:2,Z:3} → [I;1,2,3]
        for key in list(value.keys()):
            if key in BLOCK_POSITION_FIELDS:
                inner = value[key]
                if isinstance(inner, SnbtCompound) and {"X", "Y", "Z"} <= set(
                    inner.keys()
                ):
                    from grimmcraft_migrate.snbt import SnbtArray

                    coordinates = [inner[axis] for axis in ("X", "Y", "Z")]
                    value[key] = SnbtArray("I", list(coordinates))
                    self.transformations.append(
                        Transformation(
                            "block_position_array", f"{key}: compound → [I;x,y,z]"
                        )
                    )
                    changed = True

        # 2. nested item schema: Count/tag → count/components
        for key in list(value.keys()):
            inner = value[key]
            if key in ITEM_CONTAINER_KEYS and isinstance(inner, SnbtList):
                for entry in inner.items:
                    changed |= self._rewrite_item_entry(entry)
            else:
                changed |= self._rewrite_nested(inner)

        # An item compound can also appear directly (e.g. a single `Item`).
        if "id" in value and ("Count" in value or "tag" in value):
            changed |= self._rewrite_item_entry(value)
        return changed

    def _rewrite_item_entry(self, entry: SnbtValue) -> bool:
        """``{id,Count:1b,tag:{…}}`` → ``{id,count:1,components:{…}}``."""
        if not isinstance(entry, SnbtCompound):
            return False
        changed = False

        count = entry.pop("Count")
        if count is not None:
            entry["count"] = (
                SnbtNumber(str(count.as_int())) if isinstance(count, SnbtNumber)
                else count
            )
            changed = True

        tag = entry.pop("tag")
        if isinstance(tag, SnbtCompound):
            components = SnbtCompound()
            leftovers = SnbtCompound()
            for key, value in tag.items():
                if key == "display" and isinstance(value, SnbtCompound):
                    mapped: dict[str, SnbtValue] = {}
                    self._migrate_display(value, mapped, leftovers)
                    for name, component in mapped.items():
                        components[name] = component
                        components.quoted_keys.add(name)
                    continue
                rule = COMPONENT_RULES.get(key)
                if rule is None:
                    leftovers[key] = value
                    self.unknown_keys.append(key)
                    continue
                components[rule.component] = rule.transform(value)
                components.quoted_keys.add(rule.component)
            if leftovers.entries:
                components[CUSTOM_DATA_COMPONENT] = leftovers
                components.quoted_keys.add(CUSTOM_DATA_COMPONENT)
            entry["components"] = components
            self.transformations.append(
                Transformation("nested_item_schema", "Count/tag → count/components")
            )
            changed = True
        elif count is not None:
            self.transformations.append(
                Transformation("nested_item_schema", "Count → count")
            )
        return changed


def migrate_command(command: str) -> MigrationResult:
    """Migrate a single command string — the one-shot convenience entry point."""
    return CommandMigrator().migrate_command(command)
