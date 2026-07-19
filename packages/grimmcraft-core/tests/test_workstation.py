"""Workstations: derived menu titles, and the one station that overrides."""

from __future__ import annotations

import pytest

from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.entity.player import Player
from grimmcraft_core.workstation import (
    Anvil,
    BrewingStand,
    CoreWorkstation,
    CraftingTable,
    EnchantingTable,
    Furnace,
)

AT = Coordinates(0.0, 64.0, 0.0)
STATIONS = [Furnace, Anvil, BrewingStand, CraftingTable, EnchantingTable]


@pytest.mark.parametrize(
    ("station_type", "title"),
    [
        (Furnace, "Furnace"),
        (Anvil, "Anvil"),
        (BrewingStand, "Brewing Stand"),
        (CraftingTable, "Crafting Table"),
    ],
)
def test_the_title_is_derived_from_the_block(
    station_type: type[CoreWorkstation], title: str
) -> None:
    """`minecraft:crafting_table` -> "Crafting Table", so no subclass restates it."""
    assert station_type(position=AT).menu_title() == title


def test_the_enchanting_table_overrides_its_title() -> None:
    """The game titles this menu "Enchant", which the derivation cannot know."""
    assert EnchantingTable(position=AT).menu_title() == "Enchant"


@pytest.mark.parametrize("station_type", STATIONS)
def test_interacting_records_the_current_user(station_type: type[CoreWorkstation]) -> None:
    station = station_type(position=AT)
    player = Player(position=AT, name="alice")
    assert station.current_user is None
    station.interact(player)
    assert station.current_user is player


@pytest.mark.parametrize("station_type", STATIONS)
def test_every_station_knows_its_block(station_type: type[CoreWorkstation]) -> None:
    assert station_type(position=AT).block_type.string_id.startswith("minecraft:")
