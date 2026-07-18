"""The generated registry enums: shape, id hygiene, and reverse lookup.

These guard *regeneration*, which is where this package's risk lives — the enums
are rebuilt wholesale from upstream by ``_generate/``, so a bad run can silently
reshape the ids the compiler validates against.
"""

from __future__ import annotations

import re

import pytest

from grimmcraft_data import (
    Biome,
    Block,
    Effect,
    Enchantment,
    Entity,
    Food,
    Instrument,
    Item,
    Particle,
)

#: Every enum that maps one member per registry entry.
ENUMS = [Biome, Block, Effect, Enchantment, Entity, Food, Instrument, Item, Particle]

#: A namespaced Minecraft id, as the game actually writes it.
RESOURCE_ID = re.compile(r"^minecraft:[a-z0-9_./-]+$")


@pytest.mark.parametrize("enum", ENUMS, ids=lambda e: e.__name__)
def test_enum_is_populated(enum: type) -> None:
    # A generator that fetched nothing still emits a valid, empty enum.
    assert len(list(enum)) > 0


@pytest.mark.parametrize("enum", ENUMS, ids=lambda e: e.__name__)
def test_string_ids_are_unique(enum: type) -> None:
    ids = [m.string_id for m in enum]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("enum", ENUMS, ids=lambda e: e.__name__)
def test_reverse_lookup_by_numeric_id(enum: type) -> None:
    # The docstring advertises `Item(893)`; it breaks if _value_ stops being the id.
    for member in enum:
        assert enum(member.value) is member


@pytest.mark.parametrize("enum", ENUMS, ids=lambda e: e.__name__)
def test_string_ids_are_wellformed(enum: type) -> None:
    bad = [m.string_id for m in enum if not RESOURCE_ID.match(m.string_id)]
    assert not bad, f"{enum.__name__} has non-conforming ids: {bad[:5]}"


def test_effect_ids_are_snake_case() -> None:
    # Regression: upstream effects.json spells names in CamelCase ("MiningFatigue")
    # where blocks/items use snake_case, and the generator used to interpolate it
    # verbatim -- yielding "minecraft:MiningFatigue", which the game rejects.
    assert Effect.MINING_FATIGUE.string_id == "minecraft:mining_fatigue"
    assert Effect.SPEED.string_id == "minecraft:speed"


@pytest.mark.parametrize(
    "member,string_id,num_id",
    [
        (Block.STONE, "minecraft:stone", 1),
        (Block.AIR, "minecraft:air", 0),
        (Item.CHEST, "minecraft:chest", 331),
        (Item.AIR, "minecraft:air", 0),
    ],
)
def test_known_members_are_stable(member, string_id: str, num_id: int) -> None:
    # Numeric ids move between Minecraft versions; these pin the current table so
    # an unintended version bump in the generated data is loud rather than silent.
    assert member.string_id == string_id
    assert member.value == num_id


def test_block_reflects_the_1_21_grass_rename() -> None:
    # 1.20.3 renamed minecraft:grass -> minecraft:short_grass. The compiler's
    # rename diagnostic is asserted against this data, so pin it here too.
    ids = {b.string_id for b in Block}
    assert "minecraft:short_grass" in ids
    assert "minecraft:grass" not in ids


def test_member_names_are_valid_identifiers() -> None:
    # member_name() mangles ids that would be illegal Python; if that regresses,
    # the module still imports but attribute access breaks for those members.
    for enum in ENUMS:
        for member in enum:
            assert member.name.isidentifier(), f"{enum.__name__}.{member.name}"
