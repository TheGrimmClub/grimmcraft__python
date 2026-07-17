# Task: generate richer data loaders + exhaustive registry enums
> [\] TODO: execute PROMPT__ADVANCED.md
 
This extends the `_generate/{type}.py` enum generators.

**Location & naming.** Put every generator script from this task in the
`_generate/` folder inside the package (e.g.
`packages/grimmcraft-data/src/grimmcraft_data/_generate/`), and name each one
`advanced_{TYPE_KEY}.py` — where `{TYPE_KEY}` is the loader name listed in each
section (`recipe`, `loot`, `collision_shape`, `attribute`, `language`,
`registry`). Create `_generate/` (with an `__init__.py`) if it doesn't exist.

**Where generated output goes.** The *generated importable modules* and the
bundled `data/` assets belong at the package root (one level up from
`_generate/`), so callers can do `from grimmcraft_data import recipe`. Use
`OUTPUT_PATH = Path(__file__).parent.parent / "{TYPE_KEY}.py"` and write data
under `Path(__file__).parent.parent / "data" / ...`. (Adjust if the package
already uses a different data layout.)

Reuse the existing conventions where they apply: same `BASE`/`dataPaths`
resolution (`{BASE}/{rel}/{file}.json`, the value is a directory), same
`member_name()` sanitizer, stdlib only, 30s request timeout, `--list`/version
CLI.

**Before writing any parser, fetch the target JSON for the pinned version and
inspect its actual shape.** minecraft-data reshapes fields between versions;
build the parser around what you observe, not assumptions below (they are a
guide, not a contract). Emit `None` for missing optional fields; never crash on
a missing key.

---

## Part A — richer data (NOT enums: dataclasses + bundled JSON)

These datasets are large and/or structural, so do NOT inline them into `.py`.
Instead each `_generate/advanced_{name}.py` must:

1. Download the source JSON for the chosen version.
2. Save it verbatim into the package data dir: `data/{version}/{file}.json`
   at the package root (create dirs as needed). This is the shipped asset.
3. Generate a typed accessor module `{name}.py` next to the script containing:
   - `@dataclass(frozen=True, slots=True)` types for the records,
   - a loader that reads the bundled JSON via
     `importlib.resources.files(__package__).joinpath("data/...")` (lazy,
     cached with `functools.lru_cache`),
   - lookups keyed the way callers actually need (see each item),
   - cross-references to the existing enums by id where natural (e.g. a recipe
     result resolves to `Item`), but degrade gracefully to the raw id if the
     enum member is absent.

Generate these `{name}` loaders:

- **recipe** ← `recipes.json`. Top-level object keyed by result item id (string
  keys, numeric item ids). Each value is a list of recipes; a recipe is either
  shapeless (`ingredients: [...]`) or shaped (`inShape: [[...]]`), plus
  `result: {id, count}` (older versions may use bare ids / `metadata`).
  Provide: `Recipe` dataclass (result_item, result_count, shape/ingredients),
  `recipes_for(item) -> list[Recipe]`, and `all_recipes()`.
- **loot** ← `blockLoot.json` and `entityLoot.json`. Lists of
  `{block|entity, drops: [{item, dropChance, stackSizeRange, ...}]}`.
  Provide: `Drop`/`LootTable` dataclasses, `block_loot(block)` and
  `entity_loot(entity)` keyed by string id.
- **collision_shape** ← `blockCollisionShapes.json`. Shape
  `{blocks: {name: shapeId | [shapeId,...]}, shapes: {id: [[x0,y0,z0,x1,y1,z1],...]}}`.
  Provide: `AABB` dataclass and `collision_boxes(block, state_index=0) ->
  list[AABB]` that dereferences a block (per-state if it's a list) to its AABBs.
- **attribute** ← `attributes.json`. Records like
  `{name/resource, default, min, max}`. This one is small — a frozen-dataclass
  registry keyed by resource name is fine (may inline).
- **language** ← `language.json`. Flat `{translation_key: text}`. Ship as
  bundled JSON; provide `translate(key, default=None)` and `all_keys()`. Do NOT
  inline (it's large).

Keep each generator's `main()` parallel to the enum scripts: `--list`, optional
version arg, default = latest version shipping that file.

---

## Part B — exhaustive registries from Mojang `registries.json`

minecraft-data omits many vanilla registries. The authoritative, complete source
is Mojang's data generator report `reports/registries.json`, produced by:

    java -DbundlerMainClass=net.minecraft.data.Main -jar server.jar --reports

(output at `generated/reports/registries.json`). Its shape:

    { "minecraft:sound_event": {
        "protocol_id": 12,
        "default": "minecraft:...",            # optional
        "entries": { "minecraft:entity.zombie.ambient": { "protocol_id": 0 }, ... }
      }, ... }

Write **one** generator, `_generate/advanced_registry.py`, that:

1. Takes the registries file as input — accept `--input PATH` for a local file;
   if omitted, allow `--version X.Y` to download a prebuilt copy if the project
   has a known mirror URL, otherwise print clear instructions to run the command
   above and pass `--input`. Do not hardcode an unverified download URL.
2. Takes one or more registry names (e.g. `sound_event block_entity_type
   game_event menu mob_effect villager_profession painting_variant
   banner_pattern dimension_type`), defaulting to a curated list of the ones
   minecraft-data lacks. `--list` prints every registry key found in the file.
3. For each requested registry, emits `{registry_name}.py` (via the
   `OUTPUT_PATH` pattern) with an `Enum` whose `.value` is the entry
   `protocol_id` (int) and `.string_id` is the namespaced id. Use `member_name()`
   from the enum scripts. Sort members by `protocol_id` so the file is stable.
4. Header docstring records the source, registry name, MC version, entry count,
   and that `protocol_id` is stable within a version but not across versions.

---

## Part C — Taskfile

Add a task to the existing `Taskfile.yaml` in the repo root (do NOT create a new
Taskfile — open the current one and match its `version`, style, and any existing
namespacing/`vars`). Add a task that regenerates all the advanced data by running
each `_generate/advanced_*.py` script with `uv run` (the project uses uv). Wire
`registry` to use a local `registries.json` path via a task var so it doesn't
fail when no input is provided. Example shape to adapt to the file's conventions:

```yaml
  generate:advanced-data:
    desc: Regenerate advanced Minecraft data modules (recipes, loot, registries, …)
    vars:
      PKG: packages/grimmcraft-data/src/grimmcraft_data/_generate
      REGISTRIES: '{{.REGISTRIES | default "registries.json"}}'
    cmds:
      - uv run {{.PKG}}/_generate/advanced_recipe.py
      - uv run {{.PKG}}/_generate/advanced_loot.py
      - uv run {{.PKG}}/_generate/advanced_collision_shape.py
      - uv run {{.PKG}}/_generate/advanced_attribute.py
      - uv run {{.PKG}}/_generate/advanced_language.py
      - uv run {{.PKG}}/_generate/advanced_registry.py --input {{.REGISTRIES}}
```

If the Taskfile already has a data-generation task for the enum scripts, add
these alongside it (or extend it) rather than duplicating.

## Deliverable checklist

- Each generator runs standalone and re-fetches/re-reads cleanly.
- Generated modules import without error (`python -c "import {type}"` etc.).
- Bundled JSON is added under `data/...` and included as package data
  (update `pyproject.toml`/`MANIFEST` package-data globs if needed).
- Spot-check one record per dataset (e.g. a known recipe, a known sound_event
  protocol id) against the source JSON.
- Style stays consistent with the existing `_generate/{type}.py` scripts.
- For each generator add a task in the `Taskfile.yaml`
