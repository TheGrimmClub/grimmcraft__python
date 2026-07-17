"""An in-world day/night clock, backed by a :class:`ScoreBoard`, that fires
scheduled chat events.

The clock stores elapsed game ticks in a scoreboard counter (Minecraft runs at
24000 ticks/day, with tick 0 == 06:00).  From that it derives the day number and
wall-clock ``hour``/``minute``, renders a HUD line, and fires registered
:class:`ClockEvent`\\s as time crosses their trigger.  Each fired event emits a
chat message and can run a callback — the seam the ``grimmcraft-control`` state
machine hooks into (it consumes the returned :class:`ClockFire`\\s or supplies a
callback), so this module never imports the control package.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from grimmcraft_core.scoreboard import ScoreBoard

TICKS_PER_DAY = 24000
MINUTES_PER_DAY = 1440
#: Minecraft tick 0 corresponds to 06:00, i.e. a +6h (360 min) display offset.
DAWN_OFFSET_MINUTES = 360
_TIME_COUNTER = "ticks"


class TimeOfDay(Enum):
    """Named moments of the day, each mapped to a wall-clock ``(hour, minute)``."""

    MIDNIGHT = "midnight"
    SUNRISE = "sunrise"
    BREAKFAST = "breakfast"
    NOON = "noon"
    LUNCH = "lunch"
    TEATIME = "teatime"
    SUNSET = "sunset"
    DINNER = "dinner"

    @property
    def time(self) -> tuple[int, int]:
        """The ``(hour, minute)`` this moment occurs at."""
        return _TIME_OF_DAY[self]

    @classmethod
    def at(cls, hour: int, minute: int) -> TimeOfDay | None:
        """The named moment at ``(hour, minute)``, or ``None`` if unnamed."""
        for moment, when in _TIME_OF_DAY.items():
            if when == (hour, minute):
                return moment
        return None


_TIME_OF_DAY: dict[TimeOfDay, tuple[int, int]] = {
    TimeOfDay.MIDNIGHT: (0, 0),
    TimeOfDay.SUNRISE: (6, 0),
    TimeOfDay.BREAKFAST: (8, 0),
    TimeOfDay.NOON: (12, 0),
    TimeOfDay.LUNCH: (13, 0),
    TimeOfDay.TEATIME: (16, 0),
    TimeOfDay.SUNSET: (18, 0),
    TimeOfDay.DINNER: (19, 0),
}

#: A trigger tests a ``(hour, minute)`` and returns whether it should fire.
Trigger = Callable[[int, int], bool]


@dataclass(frozen=True, slots=True)
class ClockFire:
    """The record of one event firing at a specific moment."""

    event: ClockEvent
    day: int
    hour: int
    minute: int

    @property
    def message(self) -> str:
        return self.event.message

    @property
    def stamp(self) -> str:
        """A ``Day N HH:MM`` timestamp for this firing."""
        return f"Day {self.day} {self.hour:02d}:{self.minute:02d}"


@dataclass(frozen=True, slots=True)
class ClockEvent:
    """A scheduled event: when :attr:`trigger` matches, emit :attr:`message`."""

    name: str
    message: str
    trigger: Trigger
    callback: Callable[[ClockFire], None] | None = None


@dataclass
class MinecraftClock:
    """A scoreboard-driven clock that advances time and fires scheduled events."""

    scoreboard: ScoreBoard = field(default_factory=lambda: ScoreBoard("time"))
    events: list[ClockEvent] = field(default_factory=list)
    chat_log: list[str] = field(default_factory=list)

    # --- time state ----------------------------------------------------------
    @property
    def abs_ticks(self) -> int:
        """Total elapsed game ticks since the clock started."""
        return self.scoreboard.get(_TIME_COUNTER)

    @property
    def day(self) -> int:
        """The current day number (starts at 0)."""
        return self.abs_ticks // TICKS_PER_DAY

    @property
    def _minute_of_day(self) -> int:
        day_ticks = self.abs_ticks % TICKS_PER_DAY
        return (
            day_ticks * MINUTES_PER_DAY // TICKS_PER_DAY + DAWN_OFFSET_MINUTES
        ) % MINUTES_PER_DAY

    @property
    def _absolute_minute(self) -> int:
        return self.day * MINUTES_PER_DAY + self._minute_of_day

    @property
    def hour(self) -> int:
        return self._minute_of_day // 60

    @property
    def minute(self) -> int:
        return self._minute_of_day % 60

    @property
    def time_of_day(self) -> TimeOfDay | None:
        """The named moment right now, if the time matches one exactly."""
        return TimeOfDay.at(self.hour, self.minute)

    def format_time(self) -> str:
        """The current time as ``HH:MM``."""
        return f"{self.hour:02d}:{self.minute:02d}"

    def hud(self) -> str:
        """A heads-up-display line: day, clock face, time and named moment."""
        moment = self.time_of_day
        label = f" ({moment.value.title()})" if moment else ""
        return f"🕒 Day {self.day} {self.format_time()}{label}"

    # --- mutation ------------------------------------------------------------
    def set_time(self, hour: int, minute: int = 0) -> None:
        """Set the clock to ``hour:minute`` on the current day (fires nothing)."""
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError(f"invalid time {hour:02d}:{minute:02d}")
        target = (hour * 60 + minute - DAWN_OFFSET_MINUTES) % MINUTES_PER_DAY
        day_ticks = target * TICKS_PER_DAY // MINUTES_PER_DAY
        self.scoreboard.set(_TIME_COUNTER, self.day * TICKS_PER_DAY + day_ticks)

    def advance(self, delta_ticks: int) -> list[ClockFire]:
        """Move time forward by ``delta_ticks``, firing every event crossed.

        Returns the fired events in order; each also appends a line to
        :attr:`chat_log` and runs its callback.  The control state machine can
        consume this list to drive transitions.
        """
        if delta_ticks < 0:
            raise ValueError(f"cannot advance by a negative amount: {delta_ticks}")
        start_minute = self._absolute_minute
        self.scoreboard.add(_TIME_COUNTER, delta_ticks)
        end_minute = self._absolute_minute

        fires: list[ClockFire] = []
        for absolute_minute in range(start_minute + 1, end_minute + 1):
            day, minute_of_day = divmod(absolute_minute, MINUTES_PER_DAY)
            hour, minute = divmod(minute_of_day, 60)
            for event in self.events:
                if event.trigger(hour, minute):
                    fires.append(self._fire(event, day, hour, minute))
        return fires

    def _fire(self, event: ClockEvent, day: int, hour: int, minute: int) -> ClockFire:
        fire = ClockFire(event=event, day=day, hour=hour, minute=minute)
        self.chat_log.append(f"[{fire.stamp}] {event.message}")
        if event.callback is not None:
            event.callback(fire)
        return fire

    # --- event registration --------------------------------------------------
    def add_event(self, event: ClockEvent) -> ClockEvent:
        """Register a fully-built :class:`ClockEvent`."""
        self.events.append(event)
        return event

    def on_time(
        self,
        hour: int,
        minute: int,
        message: str,
        *,
        name: str | None = None,
        callback: Callable[[ClockFire], None] | None = None,
    ) -> ClockEvent:
        """Fire once per day at exactly ``hour:minute``."""
        return self.add_event(
            ClockEvent(
                name=name or f"at-{hour:02d}:{minute:02d}",
                message=message,
                trigger=lambda h, m: h == hour and m == minute,
                callback=callback,
            )
        )

    def on_hour(
        self,
        hour: int,
        message: str,
        *,
        name: str | None = None,
        callback: Callable[[ClockFire], None] | None = None,
    ) -> ClockEvent:
        """Fire once per day at the top of ``hour`` (``hour:00``)."""
        return self.on_time(hour, 0, message, name=name or f"hour-{hour:02d}", callback=callback)

    def every_hour_at(
        self,
        minute: int,
        message: str,
        *,
        name: str | None = None,
        callback: Callable[[ClockFire], None] | None = None,
    ) -> ClockEvent:
        """Fire every hour at ``minute`` past the hour."""
        return self.add_event(
            ClockEvent(
                name=name or f"every-hh:{minute:02d}",
                message=message,
                trigger=lambda h, m: m == minute,
                callback=callback,
            )
        )

    def on_time_of_day(
        self,
        moment: TimeOfDay,
        message: str,
        *,
        name: str | None = None,
        callback: Callable[[ClockFire], None] | None = None,
    ) -> ClockEvent:
        """Fire once per day at a named :class:`TimeOfDay`."""
        hour, minute = moment.time
        return self.on_time(hour, minute, message, name=name or moment.value, callback=callback)
