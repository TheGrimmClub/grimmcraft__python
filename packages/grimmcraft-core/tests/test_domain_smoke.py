"""End-to-end smoke test of the core domain model.

Builds a player, moves them, stores a book, places and opens a chest, uses a
crafting table, and drives the clock through a scheduled chat event.
"""

from __future__ import annotations

from grimmcraft_core import (
    Book,
    Chest,
    Coordinates,
    CraftingTable,
    Direction,
    GameMode,
    MinecraftClock,
    Player,
    TimeOfDay,
)
from grimmcraft_data.block import Block
from grimmcraft_data.item import Item


def test_player_moves_and_carries_a_book() -> None:
    start = Coordinates(0.0, 64.0, 0.0)
    player = Player(position=start, name="Grimm", gamemode=GameMode.SURVIVAL)

    assert player.entity_type.name == "PLAYER"
    assert player.is_alive
    assert player.inventory.capacity == 36

    player.move_to(start + Direction.EAST + Direction.EAST)
    assert player.position == Coordinates(2.0, 64.0, 0.0)
    assert player.position.to_block_pos().neighbors()  # 6 neighbours

    book = Book(title="Diary", author="Grimm", pages=["day 1"])
    assert book.item_type is Item.WRITABLE_BOOK
    assert player.inventory.add(book) is True
    assert player.inventory.slots[0] is book


def test_place_chest_and_interact() -> None:
    player = Player(position=Coordinates(0.0, 64.0, 0.0))
    chest = Chest()
    assert not chest.is_placed

    chest.place(Coordinates(3.0, 64.0, 0.0))
    assert chest.is_placed
    assert chest.capacity == 27

    assert chest.add(Book(title="loot")) is True
    chest.interact(player)
    assert chest.last_opened_by is player


def test_crafting_table_interaction_and_seam() -> None:
    player = Player(position=Coordinates(0.0, 64.0, 0.0))
    table = CraftingTable(position=Coordinates(4.0, 64.0, 0.0))

    assert table.block_type is Block.CRAFTING_TABLE
    table.interact(player)
    assert table.current_user is player

    table.place(Book(title="ingredient"), 1, 1)
    assert table.grid[1][1] is not None
    # No recipe resolver wired -> the crafting seam yields nothing, not an error.
    assert table.craft() is None


def test_health_is_clamped_and_adjusts() -> None:
    player = Player(position=Coordinates(0.0, 0.0, 0.0), health=999.0)
    assert player.health == 20.0  # clamped to max_health

    player.damage(5.0)
    assert player.health == 15.0
    player.heal(100.0)
    assert player.health == 20.0


def test_clock_fires_scheduled_chat_event() -> None:
    clock = MinecraftClock()
    clock.set_time(11, 59)
    hits: list[str] = []
    clock.on_time_of_day(
        TimeOfDay.NOON, "It is high noon.", callback=lambda fire: hits.append(fire.stamp)
    )

    fires = clock.advance(200)  # 200 ticks == 12 in-game minutes -> crosses 12:00

    assert clock.hour == 12
    assert any(fire.event.message == "It is high noon." for fire in fires)
    assert len(hits) == 1
    assert clock.chat_log and "high noon" in clock.chat_log[-1]
    assert clock.hud().startswith("🕒 Day 0 12:")
