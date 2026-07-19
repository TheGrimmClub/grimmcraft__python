"""Boss bars: a value out of a maximum, shown large, to a chosen audience."""

from __future__ import annotations

import pytest

from grimmcraft_core.bossbar import BossBar, BossBarColor, BossBarSet, BossBarStyle
from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.entity.player import Player
from grimmcraft_core.hud import Hud
from grimmcraft_core.text import Text


@pytest.fixture
def bar() -> BossBar:
    return BossBar("village:harvest", "Harvest", value=3, max_value=5)


@pytest.fixture
def alice() -> Player:
    return Player(position=Coordinates(0.0, 64.0, 0.0), name="alice")


@pytest.fixture
def bob() -> Player:
    return Player(position=Coordinates(0.0, 64.0, 0.0), name="bob")


# --- the value ---------------------------------------------------------------


def test_progress_and_percent(bar: BossBar) -> None:
    assert bar.progress == pytest.approx(0.6)
    assert bar.percent == 60


def test_a_value_past_the_end_is_clamped_not_rejected(bar: BossBar) -> None:
    """Matches CoreEntity clamping health: a full bar beats a stopped program."""
    bar.set_value(99)
    assert bar.value == 5
    assert bar.is_full


def test_a_negative_value_is_clamped_to_empty(bar: BossBar) -> None:
    bar.set_value(-99)
    assert bar.value == 0
    assert bar.is_empty


def test_the_constructor_clamps_too() -> None:
    assert BossBar("x:y", value=1000, max_value=10).value == 10


def test_add_counts_up_and_down(bar: BossBar) -> None:
    assert bar.add(1).value == 4
    assert bar.add(-2).value == 2


def test_setters_chain(bar: BossBar) -> None:
    assert bar.set_value(1).add(1).set_max(10) is bar


def test_a_maximum_below_one_is_rejected() -> None:
    """Matches SlotContainer rejecting a capacity below 1: nothing to clamp against."""
    with pytest.raises(ValueError, match="max_value must be at least 1"):
        BossBar("x:y", max_value=0)
    with pytest.raises(ValueError, match="max_value must be at least 1"):
        BossBar("x:y").set_max(-3)


def test_lowering_the_maximum_reclamps_the_value(bar: BossBar) -> None:
    bar.set_value(5).set_max(2)
    assert bar.value == 2


# --- name and style ----------------------------------------------------------


def test_a_string_name_becomes_text(bar: BossBar) -> None:
    """Names are text components, so they can be styled like any other text."""
    assert isinstance(bar.name, Text)
    assert str(bar.name) == "Harvest"


def test_a_text_name_passes_through() -> None:
    styled = Text("Boss", color="red", bold=True)
    assert BossBar("x:y", styled).name is styled


@pytest.mark.parametrize(
    ("style", "notches"),
    [
        (BossBarStyle.PROGRESS, None),
        (BossBarStyle.NOTCHED_6, 6),
        (BossBarStyle.NOTCHED_10, 10),
        (BossBarStyle.NOTCHED_12, 12),
        (BossBarStyle.NOTCHED_20, 20),
    ],
)
def test_notch_counts(style: BossBarStyle, notches: int | None) -> None:
    assert style.notches == notches


def test_there_are_exactly_seven_colours() -> None:
    """The game allows no others, so neither does this."""
    assert len(BossBarColor) == 7


# --- the audience ------------------------------------------------------------


def test_showing_and_hiding(bar: BossBar, alice: Player, bob: Player) -> None:
    bar.show_to(alice)
    assert bar.is_shown_to(alice)
    assert not bar.is_shown_to(bob)

    bar.hide_from(alice)
    assert not bar.is_shown_to(alice)


def test_showing_twice_lists_once(bar: BossBar, alice: Player) -> None:
    bar.show_to(alice).show_to(alice)
    assert bar.viewers == [alice.uuid]


def test_hiding_someone_who_never_saw_it_is_harmless(bar: BossBar, alice: Player) -> None:
    bar.hide_from(alice)
    assert bar.viewers == []


def test_an_invisible_bar_is_shown_to_nobody(bar: BossBar, alice: Player) -> None:
    """`visible` is global; the viewer list is per player. Both must hold."""
    bar.show_to(alice)
    bar.visible = False
    assert not bar.is_shown_to(alice)
    assert alice.uuid in bar.viewers, "still listed, just not currently drawn"


def test_viewers_can_be_named_by_id(bar: BossBar, alice: Player) -> None:
    bar.show_to(alice.uuid)
    assert bar.is_shown_to(alice)


# --- display -----------------------------------------------------------------


def test_the_hud_segment_draws_the_proportion(bar: BossBar) -> None:
    assert bar.hud() == "▰▰▰▰▰▰▱▱▱▱ Harvest 60%"


def test_an_unnamed_bar_omits_the_label() -> None:
    assert BossBar("x:y", value=1, max_value=2).hud() == "▰▰▰▰▰▱▱▱▱▱ 50%"


def test_a_hidden_bar_renders_nothing(bar: BossBar) -> None:
    bar.visible = False
    assert bar.hud() == ""


def test_a_hidden_bar_leaves_no_gap_in_a_hud(bar: BossBar) -> None:
    """Empty segments are dropped, so a bar can sit in a HUD permanently."""
    bar.visible = False
    assert Hud().add("left").add(bar).add("right").render() == "left  │  right"


def test_a_bar_composes_into_a_hud(bar: BossBar) -> None:
    assert Hud().add(bar).render() == bar.hud()


# --- the set -----------------------------------------------------------------


def test_adding_and_getting() -> None:
    bars = BossBarSet()
    bar = bars.create("village:harvest", "Harvest", max_value=5)
    assert bars.get("village:harvest") is bar
    assert bars.ids == ["village:harvest"]
    assert len(bars) == 1


def test_the_same_id_twice_is_an_error() -> None:
    """Unlike ender storage, a bar must be created before use -- so this is a bug."""
    bars = BossBarSet()
    bars.create("village:harvest")
    with pytest.raises(ValueError, match="already exists"):
        bars.create("village:harvest")


def test_getting_an_unknown_bar_names_it() -> None:
    with pytest.raises(KeyError, match="no boss bar with id 'village:nope'"):
        BossBarSet().get("village:nope")


def test_removing_is_forgiving() -> None:
    bars = BossBarSet()
    bars.remove("never added")
    bars.create("village:harvest")
    bars.remove("village:harvest")
    assert not bars.has("village:harvest")
    assert len(bars) == 0


def test_shown_to_filters_by_viewer(alice: Player, bob: Player) -> None:
    bars = BossBarSet()
    mine = bars.create("village:mine")
    theirs = bars.create("village:theirs")
    hidden = bars.create("village:hidden", visible=False)
    mine.show_to(alice)
    theirs.show_to(bob)
    hidden.show_to(alice)

    assert bars.shown_to(alice) == [mine]
    assert bars.shown_to(bob) == [theirs]


def test_a_set_is_iterable_and_clearable() -> None:
    bars = BossBarSet()
    bars.create("a:one")
    bars.create("a:two")
    assert [bar.bar_id for bar in bars] == ["a:one", "a:two"]
    bars.clear()
    assert len(bars) == 0


# --- the package surface -----------------------------------------------------


def test_every_exported_name_actually_exists() -> None:
    """This has broken three times: a name added to __all__ but never imported.

    ``from grimmcraft_core import *`` would fail on it, and nothing else notices.
    """
    import grimmcraft_core

    missing = [name for name in grimmcraft_core.__all__ if not hasattr(grimmcraft_core, name)]
    assert missing == []


def test_nothing_is_exported_twice() -> None:
    import grimmcraft_core

    duplicates = {n for n in grimmcraft_core.__all__ if grimmcraft_core.__all__.count(n) > 1}
    assert duplicates == set()


def test_everything_imported_is_also_exported() -> None:
    """The other direction, which the test above missed and ruff caught.

    A name imported into the package but left out of ``__all__`` is invisible to
    ``import *`` and is reported as an unused import -- which is how the boss bar
    and HUD names were found to be missing.
    """
    import __future__

    import grimmcraft_core

    public = {
        name
        for name, value in vars(grimmcraft_core).items()
        if not name.startswith("_")
        # submodules are reachable as attributes without being exports, and
        # `annotations` is the __future__ import, not a name anyone wants
        and not isinstance(value, type(grimmcraft_core) | __future__._Feature)
    }
    assert public - set(grimmcraft_core.__all__) == set()
