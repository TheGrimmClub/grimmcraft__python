# Open items — 2026

Work that is deliberately unfinished, and why. Each item says what exists, what
blocks it, and what the next move is — so picking one up does not start with
re-deriving the situation.

Last updated: 2026-07-19.

---

## 1. Mounts — `Rideable` is landed but unwired

**State.** `occupiable/rideable.py` exists, type-checks and lints clean, and
**nothing imports it**. It is the seat-owning behaviour (seats, boarding,
carry-on-move) extracted from `Vehicle` so it can be mixed into a mob as well.

**Why it exists.** A horse cannot be a `Vehicle`. The generated registry files
rideable animals as mobs, not vehicles:

| Entity | `type` | `category` |
|---|---|---|
| `HORSE`, `CAMEL`, `DONKEY`, `MULE`, `PIG` | `animal` | `Passive mobs` |
| `STRIDER` | `animal` | `Hostile mobs` |
| `OAK_BOAT`, `MINECART` | `other` | `Vehicles` |

`Vehicle.__post_init__` rejects anything whose category is not `Vehicles`, and
should keep doing so. A horse is a `Mob` — AI, health, drops, breeding. This is
the same orthogonality argument the trait itself was built on, one level up:
"carries passengers" is independent of "is a vehicle" vs "is a mob".

**Next move.**

1. Refactor `vehicle.py` to `class Vehicle(Rideable, CoreEntity)`, deleting its
   now-duplicated copy of the seat logic. The mixin must come **first** in the
   bases so its `move_to` runs before the entity's and can settle the seats
   after; written the other way round the passengers never move.
2. Add `occupiable/mount.py` — `class Mount(Rideable, Mob)`, then `Horse`,
   `Pig`, `Strider`, `Camel`. Camel takes two seats and is the reason
   `seat_offsets` is a tuple rather than a count.
3. A saddle requirement hangs off `boarding_refusal_reason`, which `Rideable`
   already exposes for exactly this — override, defer upwards, add
   `"not saddled"`. `Item.SADDLE` exists in `grimmcraft-data`.
4. Tests, matching `test_vehicle.py`.

**Watch for.** `board` must refuse anyone already aboard — a seat only knows
whether *it* is taken, so a passenger in the front seat gets accepted into the
back one as well. That was a real bug in the first draft of `Vehicle.board` and
`Rideable` carries the fix; keep the test that names it.

---

## 2. The bed's point-of-interest half — genuinely blocked

**State.** `Bed` is a `PlaceableBlock` + `Sleepable`: one sleeper, refuses a
second, refuses in daylight, refuses when unplaced, evicts on break. That half
is done and tested.

**Blocked.** The brief also asked for villager POI claiming, village population,
player respawn point, and night-skip. None of the abstractions exist. Verified
by walking all 189 source files (a `git grep` with a `packages/*/srcs/`
pathspec silently matches nothing — do not trust it):

- `PointOfInterest`, `poi`, `claim` — **no hits**
- `village`, `population`, `breed` — **no hits**
- `respawn`, `spawn_point` — **no hits**
- `skip_night`, `sleep` — **no hits**
- a per-object `tick()` — **none**; `MinecraftClock.advance()` moves world
  time but nothing subscribes to it
- `grimmcraft-npc` is dialogue only; its "village" hits are a namespace string

The brief says to stop and report rather than reimplement, so this stays
unbuilt. It attaches to `Bed` from outside when those systems arrive — nothing
in `Bed` needs rewriting to accept them.

**Also worth knowing.** There is no base `Block` type. `Block` in
`grimmcraft-data` is an enum of ids; `PlaceableBlock` (in `item/storage.py`,
extending `CoreItem`) is the only structural block class, and is what `Bed`
builds on. A real `Block` base is arguably the missing abstraction underneath
the POI gap too.

---

## 3. Boats and minecarts that move on their own

**State.** `Boat` and `Minecart` carry their passengers when *they* are asked to
move — `move_to`/`teleport` settle the seats. Nothing makes a minecart roll down
a rail.

**Blocked on the same gap as above:** there is no ticking or movement-event
system. When one arrives, the `carry_passengers()` call relocates into it and
`Seat`/`Rideable` do not change.

---

## 4. The `.pth` / iCloud problem — now blocking, not cosmetic

This repo lives under `~/Desktop`, which is iCloud-synced. iCloud sets
`UF_HIDDEN` on uv's editable `.pth` files, and CPython's `site.py` silently
skips hidden `.pth` files — so `uv run pytest` fails with
`ModuleNotFoundError: No module named 'grimmcraft_*'` even though `uv sync`
succeeded.

**It has got worse.** iCloud now re-hides the files *within a single shell
command*, so `chflags nohidden … && pytest` no longer wins the race and
`task test`'s `fix-venv` dependency is effectively broken. Conflict copies are
accumulating too (`grimmcraft_data 6.pth`, `grimmcraft_redstone 6.pth`).

**Workaround that does work:**

```sh
export PYTHONPATH=$(ls -d packages/*/srcs | tr '\n' ':')
```

**Proper fix:** move the venv off iCloud with
`UV_PROJECT_ENVIRONMENT=<non-iCloud path>`, or move the project. This is now
worth doing.

---

## 5. grimmoire — deployed, worth checking

`06661b7` (setup chapter, uv-based build) and `1bc60b4` (theme features fix,
content tabs, language switcher) are pushed to
[TheGrimmClub/grimmoire](https://github.com/TheGrimmClub/grimmoire).

**Verify by hand**, because these are runtime-JS features that cannot be checked
from the built HTML:

- the header language button switches between `en/` and `de/`
- linked tabs sync — picking Windows in "Die Installation" should switch
  "Prüfen, ob es geklappt hat" too, and persist to the next page
- code-block copy buttons now appear (they never did before the features fix)
- **the Pages deploy is green** — the workflow changed to `astral-sh/setup-uv`
  and `uv sync --frozen`, and has not run since

**Two checkouts have diverged.** The submodule at
`grimmcraft__python/grimmoire` and the standalone `../grimmoire` are separate
working copies of the same repo; the standalone one is behind. Reconcile before
anyone edits the wrong one.

**Structural question, deliberately not taken.** The sidebar still lists both
languages, because those sections are what enumerate the chapters — the header
button is the fast switch, the sections are how you browse. Showing only the
current language means two builds with a `docs_dir` per language, or an i18n
plugin. More machinery, and it splits one site into two.

---

## 6. Server configuration — investigated, not started

Making `ops.json` and friends controllable from the `grimmcraft-cli` package.

**What is already there.** `grimmcraft__fabric/Taskfile.yaml` solves part of it:
an `OP_PLAYER` var feeding an inline `python3` heredoc that resolves a Mojang
UUID (checking `usercache.json` first, then `api.mojang.com`) and writes
`ops.json`, plus EULA acceptance. That script is the natural seed for the CLI.

**Constraints found.**

- `run/` is entirely gitignored, so all server config is ephemeral — the server
  rewrites `server.properties` on shutdown and `ops.json` on `/op`. Whether the
  tool declares-and-overwrites or reconciles is *the* design decision.
- Every list file is currently `[]`; `enable-rcon=false` with an empty
  `rcon.password`; `online-mode=true`, which is what makes UUID resolution a
  network call rather than a derivation.
- `packages/grimmcraft-cli` is still a 34-line greeting scaffold;
  `PROMPT__MINECRAFT.md` is unexecuted.
- Secrets: the RCON password lives in `server.properties` and must not be
  committed.

---

## 7. Unresolved

**"ignore sesting"** — asked for during the occupiables work and never
clarified. Plausibly *testing*, *seating* or *nesting*, which imply different
things. Ask before acting on it.
