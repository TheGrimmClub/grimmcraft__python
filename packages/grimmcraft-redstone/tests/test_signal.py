from grimmcraft_redstone.signal import (
    MAX_POWER,
    OFF,
    PowerKind,
    Signal,
    clamp_power,
    game_ticks,
    redstone_ticks,
)


def test_clamp_power() -> None:
    assert clamp_power(-3) == 0
    assert clamp_power(20) == 15
    assert clamp_power(7) == 7


def test_level_zero_is_none_kind() -> None:
    assert Signal(0, PowerKind.STRONG).kind is PowerKind.NONE
    assert not Signal(0, PowerKind.STRONG).is_on


def test_is_on_and_strong() -> None:
    assert Signal.strong().is_on
    assert Signal.strong().is_strong
    assert not Signal.weak().is_strong
    assert not OFF.is_on


def test_attenuate_loses_one_per_block_and_goes_weak() -> None:
    sig = Signal.strong(15)
    assert sig.attenuate(1) == Signal(14, PowerKind.WEAK)
    assert sig.attenuate(15) == OFF
    assert sig.attenuate(1).kind is PowerKind.WEAK


def test_signal_ordering_takes_strongest() -> None:
    assert max(Signal.weak(5), Signal.weak(9)).level == 9
    # strong beats weak at equal level
    assert max(Signal.weak(9), Signal.strong(9)).kind is PowerKind.STRONG


def test_tick_conversions() -> None:
    assert redstone_ticks(1) == 2
    assert redstone_ticks(4) == 8
    assert game_ticks(3) == 3
    assert MAX_POWER == 15
