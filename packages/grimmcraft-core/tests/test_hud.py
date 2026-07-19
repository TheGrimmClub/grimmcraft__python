"""The HUD and its waypoint compass.

Most of these are really about Minecraft's yaw convention, which runs clockwise
from *south* while an ordinary compass runs clockwise from north. Getting that
backwards points a player the opposite way and still looks plausible, so it is
pinned down from several angles.
"""

from __future__ import annotations

import pytest

from grimmcraft_core.clock import MinecraftClock
from grimmcraft_core.coordinates import Coordinates, Direction
from grimmcraft_core.hud import (
    ARRIVAL_DISTANCE,
    Bearing,
    Compass,
    Hud,
    Waypoint,
    bearing_to,
    compass_point,
    facing_direction,
    horizontal_distance,
    normalize_yaw,
    turn_to,
)

ORIGIN = Coordinates(0.0, 64.0, 0.0)

#: (name, offset, expected yaw, expected point, expected face)
CARDINALS = [
    ("south", (0.0, 10.0), 0.0, "S", Direction.SOUTH),
    ("west", (-10.0, 0.0), 90.0, "W", Direction.WEST),
    ("north", (0.0, -10.0), -180.0, "N", Direction.NORTH),
    ("east", (10.0, 0.0), -90.0, "E", Direction.EAST),
]


def at(dx: float, dz: float) -> Coordinates:
    return Coordinates(ORIGIN.x + dx, ORIGIN.y, ORIGIN.z + dz)


# --- the yaw convention ------------------------------------------------------


@pytest.mark.parametrize(("name", "offset", "yaw", "point", "face"), CARDINALS)
def test_each_cardinal_direction_gets_the_right_yaw(
    name: str, offset: tuple[float, float], yaw: float, point: str, face: Direction
) -> None:
    """Minecraft: yaw 0 is +Z (south), 90 is -X (west), 180 is -Z, 270 is +X."""
    measured = bearing_to(ORIGIN, at(*offset))
    assert measured == pytest.approx(yaw)
    assert compass_point(measured) == point
    assert facing_direction(measured) is face


def test_the_diagonals_land_on_the_eight_points() -> None:
    """+X is east and +Z is south, so (+10, +10) is south-east."""
    assert compass_point(bearing_to(ORIGIN, at(10, 10))) == "SE"
    assert compass_point(bearing_to(ORIGIN, at(-10, 10))) == "SW"
    assert compass_point(bearing_to(ORIGIN, at(10, -10))) == "NE"
    assert compass_point(bearing_to(ORIGIN, at(-10, -10))) == "NW"


@pytest.mark.parametrize(
    ("raw", "folded"),
    [(0.0, 0.0), (180.0, -180.0), (190.0, -170.0), (-190.0, 170.0), (360.0, 0.0), (540.0, -180.0)],
)
def test_yaw_is_folded_into_the_range_minecraft_reports(raw: float, folded: float) -> None:
    assert normalize_yaw(raw) == pytest.approx(folded)


def test_distance_ignores_height() -> None:
    """A waypoint 200 out and 60 up is 200 away, as the in-game compass has it."""
    assert horizontal_distance(ORIGIN, Coordinates(200.0, 124.0, 0.0)) == pytest.approx(200.0)


# --- turning -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("facing", "target", "expected"),
    [
        (0.0, 0.0, 0.0),
        (0.0, 90.0, 90.0),
        (0.0, -90.0, -90.0),
        (170.0, -170.0, 20.0),  # the short way across the wrap
        (-170.0, 170.0, -20.0),
    ],
)
def test_turn_takes_the_shorter_way_round(facing: float, target: float, expected: float) -> None:
    """Never "turn 340 degrees" when 20 the other way is the same place."""
    assert turn_to(facing, target) == pytest.approx(expected)


def test_turn_is_none_without_a_facing() -> None:
    """There is no left or right until you know which way you are looking."""
    assert Bearing(yaw=90.0, distance=10.0).turn is None


# --- bearings ----------------------------------------------------------------


def test_a_bearing_describes_itself() -> None:
    bearing = Bearing(yaw=-90.0, distance=42.4, facing=-90.0)
    assert bearing.point == "E"
    assert bearing.arrow == "↑", "facing the target means straight ahead"
    assert str(bearing) == "↑ E 42m"


def test_a_bearing_behind_you_points_back() -> None:
    bearing = Bearing(yaw=0.0, distance=50.0, facing=-180.0)
    assert bearing.arrow == "↓"


def test_arriving_is_reported_as_being_there() -> None:
    assert Bearing(yaw=0.0, distance=ARRIVAL_DISTANCE).has_arrived
    assert str(Bearing(yaw=0.0, distance=0.5)) == "here"
    assert not Bearing(yaw=0.0, distance=ARRIVAL_DISTANCE + 0.1).has_arrived


def test_without_a_facing_the_arrow_is_absolute_not_relative() -> None:
    """Falling back to the compass direction beats inventing a left or right."""
    assert Bearing(yaw=-180.0, distance=10.0).arrow == "↑"  # north is "up"
    assert Bearing(yaw=0.0, distance=10.0).arrow == "↓"  # south is "down"


# --- waypoints ---------------------------------------------------------------


def test_a_waypoint_reports_where_it_is_from_here() -> None:
    home = Waypoint("Home", at(0, 100))
    bearing = home.bearing_from(ORIGIN)
    assert bearing.point == "S"
    assert bearing.distance == pytest.approx(100.0)


def test_a_waypoint_renders_a_hud_segment() -> None:
    home = Waypoint("Home", at(0, 250))
    assert home.hud_from(ORIGIN) == "⚑ Home ↓ S 250m"


def test_a_waypoint_can_carry_its_own_symbol() -> None:
    assert Waypoint("Mine", at(0, 10), symbol="⛏").hud_from(ORIGIN).startswith("⛏ Mine")


# --- the compass -------------------------------------------------------------


def test_marking_and_recalling_a_waypoint() -> None:
    compass = Compass(origin=ORIGIN)
    compass.mark("Home", at(0, 100))
    assert compass.to("Home").distance == pytest.approx(100.0)


def test_mark_here_records_the_current_position() -> None:
    compass = Compass(origin=at(30, 40))
    marked = compass.mark_here("Camp")
    assert marked.position == at(30, 40)
    assert compass.to("Camp").has_arrived


def test_an_unknown_waypoint_says_so() -> None:
    with pytest.raises(KeyError, match="no waypoint named 'Nowhere'"):
        Compass(origin=ORIGIN).to("Nowhere")


def test_forgetting_is_forgiving() -> None:
    compass = Compass(origin=ORIGIN)
    compass.forget("never marked")  # must not raise
    compass.mark("Home", at(0, 10))
    compass.forget("Home")
    assert compass.waypoints == {}


def test_the_compass_can_point_at_a_bare_position_too() -> None:
    assert Compass(origin=ORIGIN).to(at(0, 20)).point == "S"


def test_nearest_picks_the_closest_by_horizontal_distance() -> None:
    compass = Compass(origin=ORIGIN)
    compass.mark("Far", at(0, 500))
    compass.mark("Near", at(0, 50))
    compass.mark("HighButNear", Coordinates(0.0, 300.0, 60.0))
    assert compass.nearest() is not None
    assert compass.nearest().name == "Near"


def test_nearest_is_none_when_nothing_is_marked() -> None:
    assert Compass(origin=ORIGIN).nearest() is None


def test_the_compass_moves_with_you() -> None:
    compass = Compass(origin=ORIGIN)
    compass.mark("Home", at(0, 100))
    assert compass.to("Home").distance == pytest.approx(100.0)
    compass.origin = at(0, 90)
    assert compass.to("Home").distance == pytest.approx(10.0)


def test_the_compass_hud_shows_the_heading_when_nothing_is_marked() -> None:
    assert Compass(origin=ORIGIN, facing=-180.0).hud() == "🧭 N"
    assert Compass(origin=ORIGIN).hud() == "🧭 —"


def test_the_compass_hud_prefers_the_nearest_waypoint() -> None:
    compass = Compass(origin=ORIGIN, facing=0.0)
    compass.mark("Home", at(0, 300))
    assert compass.hud() == "⚑ Home ↑ S 300m"


# --- the HUD itself ----------------------------------------------------------


def test_a_hud_joins_its_segments() -> None:
    assert Hud().add("a").add("b").render() == "a  │  b"


def test_add_chains() -> None:
    hud = Hud()
    assert hud.add("a") is hud


def test_a_hud_accepts_text_callables_and_objects() -> None:
    """The seam that lets the clock and the compass share a line.

    Neither imports the other, and this module imports neither.
    """
    clock = MinecraftClock()
    clock.set_time(8, 5)
    compass = Compass(origin=ORIGIN, facing=0.0)
    compass.mark("Home", at(0, 300))

    hud = Hud().add(clock).add(compass).add(lambda: "❤ 20").add("static")
    assert hud.render() == "🕒 Day 0 08:05  │  ⚑ Home ↑ S 300m  │  ❤ 20  │  static"


def test_empty_segments_do_not_leave_stray_separators() -> None:
    assert Hud().add("a").add("").add("b").render() == "a  │  b"


def test_an_empty_hud_renders_nothing() -> None:
    assert Hud().render() == ""
    assert str(Hud()) == ""


def test_clearing_removes_everything() -> None:
    hud = Hud().add("a").add("b")
    hud.clear()
    assert hud.render() == ""


def test_the_separator_can_be_changed() -> None:
    assert Hud(separator=" | ").add("a").add("b").render() == "a | b"
