"""Storage blocks: the shared container, the chest that doubles, the barrel that cannot."""

from __future__ import annotations

import pytest

from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.entity.player import Player
from grimmcraft_core.item.barrel import Barrel
from grimmcraft_core.item.chest import DOUBLE_CHEST_SLOTS, SINGLE_CHEST_SLOTS, Chest
from grimmcraft_core.item.core_item import CoreItem
from grimmcraft_core.item.storage import STANDARD_SLOTS, StorageBlock
from grimmcraft_data.item import Item

STORAGE_BLOCKS = [Chest, Barrel]


def an_item() -> CoreItem:
    return CoreItem(item_type=Item.STONE)


# --- capacity ----------------------------------------------------------------


def test_a_chest_holds_twenty_seven() -> None:
    assert Chest().capacity == SINGLE_CHEST_SLOTS == STANDARD_SLOTS


def test_a_double_chest_holds_fifty_four() -> None:
    assert Chest(double=True).capacity == DOUBLE_CHEST_SLOTS == 54


def test_a_barrel_holds_twenty_seven() -> None:
    assert Barrel().capacity == STANDARD_SLOTS


def test_a_barrel_cannot_be_doubled() -> None:
    """Not rejected by a check -- there is no field, so it cannot be expressed.

    This is the whole reason Barrel is a sibling of Chest rather than a variant
    of it. A `kind` field on one class would have to raise here instead.
    """
    with pytest.raises(TypeError, match="unexpected keyword argument 'double'"):
        Barrel(double=True)  # type: ignore[call-arg]


# --- the shared container behaviour ------------------------------------------


@pytest.mark.parametrize("storage_type", STORAGE_BLOCKS)
def test_storing_and_retrieving(storage_type: type[StorageBlock]) -> None:
    storage = storage_type()
    item = an_item()
    assert storage.add(item) is True
    assert storage.slots[0] is item
    assert storage.remove(0) is item
    assert storage.slots[0] is None


@pytest.mark.parametrize("storage_type", STORAGE_BLOCKS)
def test_stackable_items_merge_rather_than_taking_slots(
    storage_type: type[StorageBlock],
) -> None:
    """Twenty-seven stone do not fill twenty-seven slots -- they become one stack."""
    storage = storage_type()
    for _ in range(storage.capacity):
        assert storage.add(an_item()) is True
    assert not storage.is_full
    assert storage.slots[1] is None


@pytest.mark.parametrize("storage_type", STORAGE_BLOCKS)
def test_filling_up_with_items_that_cannot_stack(
    storage_type: type[StorageBlock],
) -> None:
    """Unstackable items take one slot each, so the container really does fill."""
    storage = storage_type()
    for _ in range(storage.capacity):
        assert storage.add(CoreItem(item_type=Item.DIAMOND_SWORD)) is True
    assert storage.is_full
    assert storage.add(CoreItem(item_type=Item.DIAMOND_SWORD)) is False, (
        "a full container refuses politely"
    )


@pytest.mark.parametrize("storage_type", STORAGE_BLOCKS)
def test_iterating_yields_every_slot(storage_type: type[StorageBlock]) -> None:
    storage = storage_type()
    assert len(list(storage)) == storage.capacity


@pytest.mark.parametrize("storage_type", STORAGE_BLOCKS)
def test_contents_are_not_shared_between_instances(storage_type: type[StorageBlock]) -> None:
    """The container is built per instance, not a mutable class default."""
    first, second = storage_type(), storage_type()
    first.add(an_item())
    assert second.slots[0] is None


# --- placement ---------------------------------------------------------------


@pytest.mark.parametrize("storage_type", STORAGE_BLOCKS)
def test_carried_then_placed(storage_type: type[StorageBlock]) -> None:
    storage = storage_type()
    assert not storage.is_placed
    storage.place(Coordinates(1.0, 64.0, 2.0))
    assert storage.is_placed
    assert storage.position == Coordinates(1.0, 64.0, 2.0)


# --- interaction -------------------------------------------------------------


@pytest.mark.parametrize("storage_type", STORAGE_BLOCKS)
def test_interacting_records_the_viewer(storage_type: type[StorageBlock]) -> None:
    storage = storage_type()
    player = Player(position=Coordinates(0.0, 64.0, 0.0))
    storage.interact(player)
    assert storage.last_opened_by is player


@pytest.mark.parametrize("storage_type", STORAGE_BLOCKS)
def test_the_last_viewer_can_be_set_at_construction(storage_type: type[StorageBlock]) -> None:
    """It used to be accepted and then silently overwritten with None."""
    player = Player(position=Coordinates(0.0, 64.0, 0.0))
    assert storage_type(last_opened_by=player).last_opened_by is player


# --- job sites ---------------------------------------------------------------


def test_a_barrel_is_a_villager_job_site() -> None:
    from grimmcraft_data import VillagerProfession

    assert Barrel().is_job_site
    assert Barrel().job_site_profession is VillagerProfession.FISHERMAN


def test_a_chest_is_not_a_job_site() -> None:
    """Standing a chest by a villager does nothing; a barrel makes a fisherman."""
    assert not Chest().is_job_site
    assert Chest().job_site_profession is None


def test_the_profession_is_read_from_the_registry_not_declared() -> None:
    """It used to be a hand-written string on Barrel, which could drift.

    Deriving it means the class cannot disagree with the data — there is no
    second copy to disagree with. This asserts the derivation, not the value.
    """
    from grimmcraft_data import profession_for_workstation

    assert Barrel().job_site_profession is profession_for_workstation(Item.BARREL.string_id)
