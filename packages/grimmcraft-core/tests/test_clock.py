"""The in-world day/night clock.

The arithmetic is the interesting part: Minecraft runs 24000 ticks per day
against 1440 wall-clock minutes, so one minute is 16⅔ ticks and tick 0 is 06:00,
not midnight. Nearly every test here is really about that conversion.
"""

from __future__ import annotations

import pytest

from grimmcraft_core.clock import (
    DAWN_OFFSET_MINUTES,
    MINUTES_PER_DAY,
    TICKS_PER_DAY,
    ClockEvent,
    ClockFire,
    MinecraftClock,
    TimeOfDay,
)
from grimmcraft_core.scoreboard import ScoreBoard


def ticks(minutes: int) -> int:
    """Exactly enough ticks to cross ``minutes`` whole minutes.

    A minute is 16 2/3 ticks, so ``int(5 * 16.66)`` is 83 ticks -- 4.98 minutes,
    one minute short. Ceiling division is the only conversion that lands on the
    minute you asked for, which is the same reason ``set_time`` uses it.
    """
    return -(-minutes * TICKS_PER_DAY // MINUTES_PER_DAY)


@pytest.fixture
def clock() -> MinecraftClock:
    return MinecraftClock()


# --- TimeOfDay ---------------------------------------------------------------


def test_every_named_moment_has_a_time() -> None:
    for moment in TimeOfDay:
        hour, minute = moment.time
        assert 0 <= hour < 24
        assert 0 <= minute < 60


def test_named_moments_are_at_distinct_times() -> None:
    """`at()` returns the first match, so duplicates would make it ambiguous."""
    times = [moment.time for moment in TimeOfDay]
    assert len(times) == len(set(times))


@pytest.mark.parametrize("moment", list(TimeOfDay))
def test_at_finds_each_moment_by_its_own_time(moment: TimeOfDay) -> None:
    assert TimeOfDay.at(*moment.time) is moment


def test_at_returns_none_for_an_unnamed_time() -> None:
    assert TimeOfDay.at(3, 47) is None


# --- reading the time --------------------------------------------------------


def test_a_fresh_clock_starts_at_dawn(clock: MinecraftClock) -> None:
    """Tick 0 is 06:00 in Minecraft, not midnight -- the offset in one test."""
    assert clock.abs_ticks == 0
    assert (clock.hour, clock.minute) == (6, 0)
    assert clock.day == 0
    assert clock.time_of_day is TimeOfDay.SUNRISE


def test_half_a_day_of_ticks_is_eighteen_hundred(clock: MinecraftClock) -> None:
    clock.advance(TICKS_PER_DAY // 2)
    assert (clock.hour, clock.minute) == (18, 0)
    assert clock.time_of_day is TimeOfDay.SUNSET


def test_the_day_number_rolls_over(clock: MinecraftClock) -> None:
    clock.advance(TICKS_PER_DAY)
    assert clock.day == 1
    assert (clock.hour, clock.minute) == (6, 0), "a full day returns to dawn"
    clock.advance(TICKS_PER_DAY * 3)
    assert clock.day == 4


def test_time_wraps_past_midnight(clock: MinecraftClock) -> None:
    """18:00 + 8h is 02:00, not 26:00."""
    clock.set_time(18, 0)
    clock.advance(ticks(8 * 60))
    assert (clock.hour, clock.minute) == (2, 0)


def test_the_day_number_rolls_at_dawn_not_at_midnight(clock: MinecraftClock) -> None:
    """A Minecraft day begins at 06:00, because tick 0 is 06:00.

    So crossing midnight does *not* increment the day: 02:00 belongs to the day
    that started the previous dawn. Worth pinning down, because "day" reads like
    a calendar date and behaves like one only if you start counting at sunrise.
    """
    clock.set_time(18, 0)
    clock.advance(ticks(8 * 60))  # -> 02:00, past midnight
    assert (clock.hour, clock.minute) == (2, 0)
    assert clock.day == 0, "still the day that began at the previous dawn"

    clock.advance(ticks(4 * 60))  # -> 06:00, the next dawn
    assert (clock.hour, clock.minute) == (6, 0)
    assert clock.day == 1


def test_format_and_hud(clock: MinecraftClock) -> None:
    clock.set_time(8, 5)
    assert clock.format_time() == "08:05"
    assert clock.hud() == "🕒 Day 0 08:05"


def test_the_hud_names_the_moment_when_there_is_one(clock: MinecraftClock) -> None:
    clock.set_time(12, 0)
    assert clock.hud() == "🕒 Day 0 12:00 (Noon)"


# --- set_time ----------------------------------------------------------------


@pytest.mark.parametrize("minute", range(60))
def test_set_time_round_trips_for_every_minute(clock: MinecraftClock, minute: int) -> None:
    """A minute is 16 2/3 ticks, so the conversion must round up, not truncate.

    Truncating lands on the tick below the boundary, which reads back as the
    previous minute: two thirds of all minutes were unreachable and
    ``set_time(6, 1)`` produced 06:00.
    """
    clock.set_time(6, minute)
    assert (clock.hour, clock.minute) == (6, minute)


@pytest.mark.parametrize("hour", range(24))
def test_set_time_round_trips_for_every_hour(clock: MinecraftClock, hour: int) -> None:
    clock.set_time(hour, 30)
    assert (clock.hour, clock.minute) == (hour, 30)


def test_set_time_keeps_the_day(clock: MinecraftClock) -> None:
    clock.advance(TICKS_PER_DAY * 2)
    clock.set_time(23, 59)
    assert clock.day == 2


def test_set_time_fires_nothing(clock: MinecraftClock) -> None:
    """Documented behaviour: setting the clock skips events rather than firing them."""
    clock.on_hour(12, "noon!")
    clock.set_time(13, 0)
    assert clock.chat_log == []


@pytest.mark.parametrize("hour, minute", [(24, 0), (-1, 0), (0, 60), (0, -1), (25, 61)])
def test_set_time_rejects_impossible_times(
    clock: MinecraftClock, hour: int, minute: int
) -> None:
    with pytest.raises(ValueError, match="invalid time"):
        clock.set_time(hour, minute)


# --- advancing and firing ----------------------------------------------------


def test_advance_rejects_going_backwards(clock: MinecraftClock) -> None:
    with pytest.raises(ValueError, match="negative"):
        clock.advance(-1)


def test_advancing_nothing_fires_nothing(clock: MinecraftClock) -> None:
    clock.on_time(6, 0, "dawn")
    assert clock.advance(0) == []


def test_an_event_does_not_fire_for_the_minute_already_reached(clock: MinecraftClock) -> None:
    """A fresh clock is at 06:00; advancing must not re-fire that minute."""
    clock.on_time(6, 0, "dawn")
    assert clock.advance(10) == []


def test_an_event_fires_when_its_minute_is_crossed(clock: MinecraftClock) -> None:
    clock.on_time(8, 0, "breakfast")
    fires = clock.advance(TICKS_PER_DAY // 4)  # 06:00 -> 12:00
    assert [fire.event.message for fire in fires] == ["breakfast"]
    assert fires[0].day == 0
    assert (fires[0].hour, fires[0].minute) == (8, 0)


def test_events_fire_in_chronological_order(clock: MinecraftClock) -> None:
    clock.on_hour(9, "nine")
    clock.on_hour(7, "seven")
    clock.on_hour(8, "eight")
    fires = clock.advance(TICKS_PER_DAY // 4)
    assert [fire.event.message for fire in fires] == ["seven", "eight", "nine"]


def test_a_daily_event_fires_once_per_day_crossed(clock: MinecraftClock) -> None:
    clock.on_hour(12, "noon")
    fires = clock.advance(TICKS_PER_DAY * 3)
    assert len(fires) == 3
    assert [fire.day for fire in fires] == [0, 1, 2]


def test_every_hour_at_fires_hourly(clock: MinecraftClock) -> None:
    clock.every_hour_at(30, "half past")
    fires = clock.advance(TICKS_PER_DAY // 4)  # six hours
    assert len(fires) == 6
    assert {fire.minute for fire in fires} == {30}


def test_firing_appends_to_the_chat_log(clock: MinecraftClock) -> None:
    clock.on_hour(12, "lunch time")
    clock.advance(TICKS_PER_DAY // 4)
    assert clock.chat_log == ["[Day 0 12:00] lunch time"]


def test_a_callback_runs_with_the_fire(clock: MinecraftClock) -> None:
    seen: list[ClockFire] = []
    clock.on_hour(12, "noon", callback=seen.append)
    fires = clock.advance(TICKS_PER_DAY // 4)
    assert seen == fires
    assert seen[0].stamp == "Day 0 12:00"


def test_a_trigger_matching_everything_fires_every_minute(clock: MinecraftClock) -> None:
    clock.add_event(ClockEvent(name="tick", message="m", trigger=lambda h, m: True))
    fires = clock.advance(ticks(5))
    assert len(fires) == 5


# --- registration ------------------------------------------------------------


def test_add_event_returns_the_event_and_registers_it(clock: MinecraftClock) -> None:
    event = ClockEvent(name="e", message="m", trigger=lambda h, m: False)
    assert clock.add_event(event) is event
    assert clock.events == [event]


def test_helpers_derive_a_readable_default_name(clock: MinecraftClock) -> None:
    assert clock.on_time(7, 5, "m").name == "at-07:05"
    assert clock.on_hour(7, "m").name == "hour-07"
    assert clock.every_hour_at(5, "m").name == "every-hh:05"
    assert clock.on_time_of_day(TimeOfDay.NOON, "m").name == "noon"


def test_an_explicit_name_wins(clock: MinecraftClock) -> None:
    assert clock.on_hour(7, "m", name="wake-up").name == "wake-up"


def test_on_time_of_day_fires_at_that_moment(clock: MinecraftClock) -> None:
    clock.on_time_of_day(TimeOfDay.DINNER, "dinner is served")
    fires = clock.advance(TICKS_PER_DAY // 2)  # 06:00 -> 18:00... plus dinner at 19:00
    assert [f.event.message for f in fires] == []
    fires = clock.advance(ticks(60))  # -> 19:00
    assert [(f.hour, f.minute) for f in fires] == [(19, 0)]


# --- wiring ------------------------------------------------------------------


def test_the_clock_reads_its_time_from_the_scoreboard() -> None:
    """The scoreboard is the single source of truth, not a cached counter."""
    board = ScoreBoard("time")
    clock = MinecraftClock(scoreboard=board)
    board.set("ticks", TICKS_PER_DAY + TICKS_PER_DAY // 4)
    assert clock.day == 1
    assert (clock.hour, clock.minute) == (12, 0)


def test_dawn_offset_is_what_makes_tick_zero_six_in_the_morning() -> None:
    assert DAWN_OFFSET_MINUTES == 6 * 60
