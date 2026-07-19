"""The stonecutter: one input, a menu of variants, and the one chosen."""

from __future__ import annotations

import pytest

from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.item.core_item import CoreItem
from grimmcraft_core.workstation import Stonecutter
from grimmcraft_data.item import Item

AT = Coordinates(0.0, 64.0, 0.0)

STONE = CoreItem(item_type=Item.STONE)
VARIANTS = [
    CoreItem(item_type=Item.STONE_SLAB),
    CoreItem(item_type=Item.STONE_STAIRS),
    CoreItem(item_type=Item.STONE_BRICKS),
]


def a_cutter(**options: object) -> Stonecutter:
    """A cutter wired to a resolver that offers the three variants above."""
    return Stonecutter(position=AT, cut_resolver=lambda _item: list(VARIANTS), **options)  # type: ignore[arg-type]


# --- the menu ----------------------------------------------------------------


def test_nothing_in_means_nothing_offered() -> None:
    assert a_cutter().options() == []


def test_an_input_offers_its_variants() -> None:
    cutter = a_cutter()
    cutter.set_input(STONE)
    assert cutter.options() == VARIANTS


def test_without_a_resolver_there_are_no_options() -> None:
    """Core ships no recipes, so an unwired cutter offers nothing rather than guessing."""
    cutter = Stonecutter(position=AT)
    cutter.set_input(STONE)
    assert cutter.options() == []
    assert cutter.cut() is None


# --- selecting ---------------------------------------------------------------


def test_the_first_variant_is_selected_by_default() -> None:
    cutter = a_cutter()
    cutter.set_input(STONE)
    assert cutter.selected == 0
    assert cutter.cut() == VARIANTS[0]


def test_selecting_picks_a_different_variant() -> None:
    cutter = a_cutter()
    cutter.set_input(STONE)
    cutter.select(2)
    assert cutter.cut() == VARIANTS[2]


def test_selecting_out_of_range_is_rejected() -> None:
    cutter = a_cutter()
    cutter.set_input(STONE)
    with pytest.raises(ValueError, match="no variant at index 9"):
        cutter.select(9)


def test_changing_the_input_resets_the_selection() -> None:
    """The menu is rebuilt, so a stale index would silently cut the wrong thing."""
    cutter = a_cutter()
    cutter.set_input(STONE)
    cutter.select(2)
    cutter.set_input(CoreItem(item_type=Item.ANDESITE))
    assert cutter.selected == 0


# --- cutting -----------------------------------------------------------------


def test_cutting_consumes_the_input() -> None:
    cutter = a_cutter()
    cutter.set_input(STONE)
    cutter.cut()
    assert cutter.input is None
    assert cutter.options() == []


def test_cutting_nothing_returns_nothing() -> None:
    assert a_cutter().cut() is None


# --- the station itself ------------------------------------------------------


def test_the_menu_title_is_derived() -> None:
    assert Stonecutter(position=AT).menu_title() == "Stonecutter"


def test_a_stonecutter_employs_a_mason() -> None:
    """Read from the generated registry, not declared here."""
    from grimmcraft_data import VillagerProfession

    cutter = Stonecutter(position=AT)
    assert cutter.is_job_site
    assert cutter.job_site_profession is VillagerProfession.MASON
