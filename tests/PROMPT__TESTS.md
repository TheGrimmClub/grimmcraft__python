# Task: generate a pytest suite for all generated data modules
> [ ] TODO: execute PROMPT__TESTS.md for data classes

Write tests covering every module produced by the generators in this package:
the enum modules (`block`, `item`, `entity`, `biome`, `effect`, `enchantment`,
`food`, `particle`, `instrument`), the registry enums from
`_generate/advanced_registry.py` (`sound_event`, `block_entity_type`,
`game_event`, `menu`, `mob_effect`, `villager_profession`, `painting_variant`,
`banner_pattern`, `dimension_type`, …), and the advanced data loaders (`recipe`,
`loot`, `collision_shape`, `attribute`, `language`).

Use **pytest**, run via `uv run pytest`. Put tests under the package's `tests/`
dir. **Tests must be hermetic — no network.** Any test that would hit the
internet must be marked `@pytest.mark.online` and skipped by default (register
the marker in `pyproject.toml` and add `addopts = "-m 'not online'"`, or use a
`--run-online` flag). Generators fetch; tests do not.

## 1. Structural invariants (parametrized over every enum module)

Build a single table of `(module_name, EnumClass)` so adding a type later is one
line, then parametrize these checks across all of them:

- Module imports without error and the enum is non-empty (assert a sane floor,
  e.g. `len(Block) > 100`, `len(Item) > 100`, others `> 0`).
- **No accidental aliasing.** Python `Enum` silently collapses members that
  share a value. Assert `len(list(EnumClass)) == len(EnumClass.__members__)` and
  that all `.value`s are unique — this catches duplicate integer ids.
- Every `.value` is an `int`; every `.string_id` is a `str` matching
  `^[a-z0-9_.]+:[a-z0-9_./]+$` and starting with `minecraft:` (unless a member
  legitimately has another namespace).
- Every member name is a valid identifier, uppercase, and unique.
- Reverse lookup by value works: `EnumClass(some_member.value) is some_member`.
- Reverse lookup by string is available and correct if the module exposes a
  `from_string()` / `_value2member_` helper (test it if present).

## 2. Authoritative cross-check against bundled JSON (preferred)

Where the module has a corresponding bundled source JSON under `data/…` (the
advanced generators save one; extend the enum generators to also save their
source JSON if that makes this feasible), load that JSON and assert:

- enum member count == number of entries in the JSON,
- for each entry, a member exists whose `.value == entry["id"]` (or
  `protocol_id` for registries) and `.string_id` matches the entry name.

This makes the test authoritative without a network call. If a module has no
bundled JSON, skip this block for it (mark `xfail`/`skip` with a clear reason)
and rely on §1 + §3.

## 3. Pinned spot-checks (a handful of stable, well-known values)

Assert a few values that effectively never change, to catch gross regressions.
Verify each against the source before committing; keep the list short. Examples:

- `Block.STONE.string_id == "minecraft:stone"`; `Block.AIR` exists.
- `Item.DIAMOND.string_id == "minecraft:diamond"`.
- `Entity.ZOMBIE.string_id == "minecraft:zombie"`.
- `Biome.PLAINS` exists.
- `collision_shape.collision_boxes("air")` is empty; `"stone"` is one full cube
  `AABB(0,0,0,1,1,1)`.
- `loot.block_loot("stone")` yields a drop of `minecraft:cobblestone`.
- `language.translate("block.minecraft.stone")` returns a non-empty string;
  an unknown key returns the supplied default.
- A known craftable resolves: `recipe.recipes_for(<known item>)` is non-empty.

## 4. Advanced-loader shape tests

- Loaders return the declared frozen dataclasses (assert `is_dataclass` and key
  fields are populated with correct types).
- `functools.lru_cache`d loaders return the same object on repeat calls.
- Bundled data resolves via `importlib.resources` (the data files are packaged).
- Attribute records satisfy `min <= default <= max`.

## 5. Optional integration / consistency (mark `online` or keep local)

- Every `recipe` result id resolves to an `Item` member; every `loot` block id
  resolves to a `Block`, entity id to an `Entity`. Report offenders; allow a
  small known-exceptions allowlist rather than hard-failing on data quirks.

## 6. Taskfile

Add/extend a task in the root `Taskfile.yaml` (match the existing style; don't
create a new file) that runs the suite, e.g.:

```yaml
  test:data:
    desc: Run the grimmcraft-data test suite
    cmds:
      - uv run pytest packages/grimmcraft-data/tests -q
```

If a general `test` task already exists, ensure it picks these up rather than
duplicating.

## Deliverable checklist

- `uv run pytest` is green locally with no network access.
- Adding a new generated type requires editing only the one parametrization
  table.
- Online/consistency tests are clearly separated and skipped by default.
