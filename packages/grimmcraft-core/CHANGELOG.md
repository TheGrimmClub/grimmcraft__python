# Changelog — grimmcraft-core

## feat(vehicle): boats and minecarts — 2026-07-19

`Vehicle` is an entity that owns seats; `Boat` has two, `Minecart` one, and that
is the whole of the difference between them.

**Moving is the event.** A seat can compute where its occupant belongs but not
*when* to put them there, and nothing in this codebase ticks. A vehicle is the
one thing that knows the moment its own position changes — it is the host — so
`move_to` and `teleport` settle its seats. Passengers are carried without any
scheduler existing. The honest boundary: a vehicle carries people when *it* is
asked to move; nothing makes a minecart roll down a rail on its own.

**The seating plan belongs to the kind, not the instance.** No boat holds three,
so `seat_offsets` is a `ClassVar` rather than a constructor argument, and it
declares the offsets rather than the count — one declaration instead of two,
where the length *is* the seat count. `Minecart` restates nothing: one seat at no
offset is already the default. A new vehicle is a subclass and a tuple.

**`board` refuses anyone already aboard.** A seat cannot catch that on its own —
it only knows whether *it* is taken, so a passenger in the front seat would
otherwise be accepted into the back one as well. There is a test for exactly
that, because it was a real bug in the first draft.

Being a vehicle is checked against `Entity.category == "Vehicles"` from the
generated registry, the way `Mob` checks `Entity.type`, so a vehicle cannot
disagree with the data about what it is.

**One thing nobody wrote:** carrying nests. A boat can ride in a minecart,
because a vehicle is an ordinary occupant; moving the cart settles its seat,
which teleports the boat, which settles its own seats in turn. A test pins it.

## feat(seat): the other half of the trait — 2026-07-19

`Seat` carries its occupant as its host moves, which is the whole of what makes
it not a bed. It overrides `occupant_position` and **nothing else** — a test
asserts that, by checking the class overrides none of `enter`, `exit`,
`refusal_reason` or `settle_occupant`. That claim previously rested on a
throwaway `Seat` defined inside `test_occupancy.py`; it is now carried by
shipped code, and the throwaway is gone.

**A host is anything `Positioned`.** A boat is an entity, a minecart is an
entity, a saddled horse is a mob, and a seat should not have to know which —
so the host is the structural protocol, which also keeps this module free of
entity imports exactly as the trait is free of block ones.

`ride_offset` puts a rider above their mount rather than inside it; left unset
the occupant shares the host's position, which is what a minecart wants.

**Nothing ticks.** `occupant_position` is computed from the host on every read,
so it is never stale, but the occupant is only teleported when
`settle_occupant()` is called — by whoever moved the host. When a movement-event
or ticking system arrives, that call relocates and this class does not change.

**A vehicle is seats, not a seat that counts.** A seat holds one, because that
is what makes "the seat is taken" a question with an answer; a boat is two
seats. A test builds that two-seater to show it needs nothing new.

## feat(bed): the bed, as a block that is also occupiable — 2026-07-19

`Bed` is a `PlaceableBlock` and a `Sleepable`, and this module is the only place
that knows it is both — which is the arrangement the occupancy trait was shaped
to allow, now with something actually using it.

**One position, not two.** `Sleepable` carries a `rest_position`, but a block
already knows where it is. Keeping both would let a bed placed here put its
sleeper there, so `occupant_position` reads the placement and `rest_position`
goes unused for a bed.

**Sleeping is refused, not raised** — the trait's rule, extended with the two a
bed owns: "not placed" (a bed in your pocket is not somewhere to sleep) and "it
is daytime". `refusal_reason` defers upwards first, so "occupied" and "already
inside" keep their wording in one place.

Night is read from the clock's own table of named moments, sunset to sunrise, so
the two cannot drift apart. It wraps midnight, which is why the test that pins
that is parametrized on both sides of it. A bed with no clock does not refuse on
time at all: not knowing the hour is not grounds for claiming it is the wrong
one.

Breaking the bed turfs the sleeper out, or the broken bed would go on refusing
everyone as still occupied.

**Still not here, deliberately:** beds are also points of interest — village
population, home claiming, respawn, night-skip. None exist, and none are needed
to hold a sleeper. They attach from outside when they arrive, the same way
occupancy does.

## feat(occupancy): the Occupiable trait — 2026-07-19

`Occupiable` holds one occupant with `enter` / `exit`, and `Sleepable` puts them
at a fixed place. Players and villagers work identically; nothing here asks
which it is.

Orthogonal on purpose. A bed is a block, a point of interest *and* occupiable; a
boat is an entity and occupiable; a minecart is neither block nor POI. Merging
occupancy into any of those hierarchies forces the other two to inherit what
they are not — so this is a mixin that knows nothing about blocks, villagers or
claiming, and a test asserts it imports none of them.

The bed/seat difference is **where the occupant is**, and nothing else. That
lives in one overridable property. A test builds a seat whose position follows a
moving host, without changing `Occupiable` — because "the seat variant drops in
without refactoring" is only worth claiming if it can be shown.

A refusal returns `False` rather than raising: something already being in the
bed is an ordinary answer. `refusal_reason` gives the why, and distinguishes
"occupied" from "already inside".


## fix(game): three real bugs, and one enum instead of two — 2026-07-19

`game.py` had a rule enum with one member, spelled wrongly, that nothing used:

- **The spelling was wrong.** `do_daylight_cycle` should be `doDaylightCycle`.
  Verified against Mojang's own data, not memory: of 63 rules, zero contain an
  underscore.
- **The enum was bypassed.** `rule()` and `set_rule()` took `str`, so
  `set_rule("doDayLightCycle", True)` type-checked and created a dead rule. They
  take `GameRule` now, which is what makes the enum worth having.
- **`rule()` raised `KeyError` for anything unset**, so reading a rule on a
  fresh session failed. It returns `None`, or a caller-supplied `default`.

Values are typed `bool | int` — the only two kinds Minecraft has, so a wider
type would let `3.7` through here and fail in game.

Two more found while in there: `ban_player` merely called `remove_player`, so a
ban lasted until the player reconnected; and `set_mode` accepted an unknown
player and silently lost the setting, though `mode()` rejects the same name.

**`GameMode` is gone; `GameModeType` is the one enum.** `player.py` defined a
second, identical copy of the same four values in the same package — the shape
that produced the duplicate `yes`.


## feat(core): rich text components

`text.py` — `Text` and `ClickEvent`, modelling Minecraft's text component: colour, the five styles, click actions (`run_command`, `suggest_command`, `open_url`, `copy_to_clipboard`, `change_page`, `show_dialog`) and a hover tooltip, with children that inherit style.

Pure data: rendering it to the version-correct syntax is the `Dialect`'s job, as with every other command. A bare `str` remains valid everywhere a component is accepted, and an unstyled `Text` renders exactly as one — so nothing existing changes.

## feat(core): the dialogue model

`entity/dialogue.py` — `Dialogue`, `Scene`, `Option`, `Condition`. Branching NPC dialogue as Ren'Py models it: named scenes that say lines, run effects, and then offer a menu, jump onwards, or end.

The data model only — pure, immutable, and free of Minecraft syntax. The builder and the lowering to a `Machine` live in `grimmcraft-npc`, because both need command constructors from `grimmcraft-control`, which depends on this package. `problems()` and `unreachable()` report structural faults as sentences, so a caller can surface them as diagnostics rather than an exception.

## feat(core): the `CommandLike` protocol

`protocols.py` gains `CommandLike` — structurally `grimmcraft_control.machine.Command`, but stated as a protocol so core's domain types can hold commands without importing `grimmcraft-control`, which depends on core and would make the two circular.

Its members are read-only properties rather than plain attributes, because `Command` is a *frozen* dataclass: a settable `name: str` could not be satisfied by any immutable type.

---

## refactor(core): standardise build on uv_build + srcs

`pyproject.toml` — switched to the `uv_build` backend with `module-root = "srcs"` so the package matches the rest of the workspace and its editable install resolves from `srcs/`.
