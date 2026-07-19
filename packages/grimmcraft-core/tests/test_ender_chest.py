"""The ender chest: one shared inventory per owner, seen through any block."""

from __future__ import annotations

import pytest

from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.entity.player import Player
from grimmcraft_core.item.core_item import CoreItem, Inventory
from grimmcraft_core.item.ender_chest import EnderChest, EnderStorage, ender_storage
from grimmcraft_core.item.storage import STANDARD_SLOTS
from grimmcraft_data.item import Item

SOMEWHERE = Coordinates(0.0, 64.0, 0.0)
FAR_AWAY = Coordinates(9999.0, 64.0, 9999.0)


@pytest.fixture
def storage() -> EnderStorage:
    """A registry of its own, so tests cannot leak into each other."""
    return EnderStorage()


@pytest.fixture
def alice() -> Player:
    return Player(position=SOMEWHERE, name="alice")


@pytest.fixture
def bob() -> Player:
    return Player(position=SOMEWHERE, name="bob")


def a_diamond(count: int = 1) -> CoreItem:
    return CoreItem(item_type=Item.DIAMOND, count=count)


# --- the shared inventory ----------------------------------------------------


def test_two_blocks_share_one_inventory_per_owner(
    storage: EnderStorage, alice: Player
) -> None:
    """The whole point: any ender chest shows the same items to the same player."""
    here = EnderChest(storage=storage)
    far = EnderChest(storage=storage)
    here.place(SOMEWHERE)
    far.place(FAR_AWAY)

    here.open(alice).add(a_diamond(3))

    assert far.open(alice) is here.open(alice)
    assert far.open(alice).slots[0] == a_diamond(3)


def test_different_owners_get_different_inventories(
    storage: EnderStorage, alice: Player, bob: Player
) -> None:
    chest = EnderChest(storage=storage)
    chest.open(alice).add(a_diamond())

    assert chest.open(bob) is not chest.open(alice)
    assert chest.open(bob).slots[0] is None, "bob sees his own, empty"


def test_an_inventory_is_twenty_seven_slots(storage: EnderStorage, alice: Player) -> None:
    inventory = EnderChest(storage=storage).open(alice)
    assert isinstance(inventory, Inventory)
    assert inventory.capacity == STANDARD_SLOTS == 27


def test_opening_by_id_works_as_well_as_by_entity(
    storage: EnderStorage, alice: Player
) -> None:
    chest = EnderChest(storage=storage)
    assert chest.open(alice.uuid) is chest.open(alice)


# --- placing and breaking move nothing ---------------------------------------


def test_breaking_a_block_leaves_the_items_alone(
    storage: EnderStorage, alice: Player
) -> None:
    here = EnderChest(storage=storage)
    far = EnderChest(storage=storage)
    here.place(SOMEWHERE)
    here.open(alice).add(a_diamond(5))

    here.break_block()

    assert not here.is_placed
    assert far.open(alice).slots[0] == a_diamond(5)


def test_breaking_every_block_still_leaves_the_items(
    storage: EnderStorage, alice: Player
) -> None:
    """Storage outlives the blocks entirely -- it was never in them."""
    chest = EnderChest(storage=storage)
    chest.place(SOMEWHERE)
    chest.open(alice).add(a_diamond(2))
    chest.break_block()
    del chest

    assert EnderChest(storage=storage).open(alice).slots[0] == a_diamond(2)


def test_placing_a_new_block_shows_the_existing_items(
    storage: EnderStorage, alice: Player
) -> None:
    EnderChest(storage=storage).open(alice).add(a_diamond())

    fresh = EnderChest(storage=storage)
    fresh.place(FAR_AWAY)
    assert fresh.open(alice).slots[0] == a_diamond()


# --- interaction -------------------------------------------------------------


def test_interacting_opens_and_records_the_viewer(
    storage: EnderStorage, alice: Player
) -> None:
    chest = EnderChest(storage=storage)
    chest.interact(alice)

    assert chest.last_opened_by is alice
    assert storage.has_owner(alice), "interacting opened alice's inventory"


def test_an_ender_chest_is_not_itself_a_container(storage: EnderStorage) -> None:
    """`add(item)` cannot be answered without knowing whose items -- so it is absent."""
    chest = EnderChest(storage=storage)
    assert not hasattr(chest, "add")
    assert not hasattr(chest, "slots")


# --- the registry ------------------------------------------------------------


def test_an_inventory_is_created_only_on_first_access(
    storage: EnderStorage, alice: Player
) -> None:
    assert not storage.has_owner(alice)
    assert len(storage) == 0

    storage.for_owner(alice)

    assert storage.has_owner(alice)
    assert storage.owners == [alice.uuid]
    assert len(storage) == 1


def test_repeated_access_returns_the_same_inventory(
    storage: EnderStorage, alice: Player
) -> None:
    assert storage.for_owner(alice) is storage.for_owner(alice)
    assert len(storage) == 1


def test_clearing_forgets_everything(storage: EnderStorage, alice: Player) -> None:
    storage.for_owner(alice).add(a_diamond())
    storage.clear()

    assert len(storage) == 0
    assert storage.for_owner(alice).slots[0] is None


def test_chests_default_to_the_world_registry(alice: Player) -> None:
    """Without an explicit registry, every ender chest shares the world's one.

    Uses its own player so it cannot disturb, or be disturbed by, other tests
    that touch the module-level storage.
    """
    solitary = Player(position=SOMEWHERE, name="only-here")
    assert EnderChest().storage is ender_storage()
    EnderChest().open(solitary).add(a_diamond(7))
    assert EnderChest().open(solitary).slots[0] == a_diamond(7)
    ender_storage().clear()


def test_separate_registries_do_not_leak(alice: Player) -> None:
    """Two worlds, or a test and the world, stay independent."""
    first, second = EnderStorage(), EnderStorage()
    EnderChest(storage=first).open(alice).add(a_diamond())
    assert EnderChest(storage=second).open(alice).slots[0] is None
