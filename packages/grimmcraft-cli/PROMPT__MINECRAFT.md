# Task: build the grimmcraft CLI — start & control Minecraft from the shell
> [ ] TODO: execute PROMPT__MINECRAFT.md 

Build a command-line tool that launches, controls, and reads data from a local
Minecraft (Java) **server**, and deploys the grimmcraft datapack to it for
testing. Put it in a package (e.g. `packages/grimmcraft-cli/src/grimmcraft_cli/`);
create it if needed and match the repo's conventions (uv, Python version,
dataclass/pydantic, layout, lint/type config, Taskfile, docs tooling).
**First inspect the sibling packages** and reuse them.

## Architecture reality (design around this)

- A Java **server** is controllable and readable from the shell; the vanilla
  **client** is not (no official remote API). So the CLI drives a server via
  **RCON**, parses its **logs**, and installs **datapacks**. Launching the
  client is a separate, optional convenience — treat it as "start the game to
  look at the result", not as something to control.
- Verify library/protocol specifics before coding (RCON = the Source RCON
  protocol; client launch via `portablemc` or `minecraft-launcher-lib`).

## Use the other packages

- **grimmcraft-compiler** — `deploy` compiles the datapack for the server's
  version/flavor, installs it into the world's `datapacks/`, and reloads.
- **grimmcraft-data** — the server version pins which enums/ids are valid;
  reuse the version/pack-format knowledge rather than duplicating it.
- Read data commands can surface `grimmcraft-core`/`grimmcraft-control` concepts
  (entity positions, machine scoreboards) as typed results where useful.

## Commands (CLI: `grimmcraft`, also `python -m grimmcraft_cli`)

Use the repo's CLI framework if one exists; else Typer (Click-based) with rich
output. Group commands:

- **server**
  - `server install --version X.Y --flavor {vanilla,paper,fabric}` — set up a
    managed server dir; download/pin the correct server jar for the flavor
    (vanilla Mojang jar, PaperMC API, Fabric server launcher). Do NOT
    auto-accept the EULA — print it and require an explicit `--accept-eula`
    (or interactive confirm); the user accepts, not the tool.
  - `server start` / `stop` / `restart` / `status` — manage the java process
    (background, PID/lock file, graceful stop via RCON `stop`), auto-enable RCON
    in `server.properties` with a generated password stored securely.
  - `server console` — attach to stdin/stdout (or tmux/screen) for a live console.
- **rcon**
  - `rcon "<command>"` — send any command, print the response.
  - `rcon shell` — interactive REPL over a persistent RCON connection.
- **data / read** (this is the "read data from the shell" story)
  - Thin wrappers that issue read commands over RCON and parse the text into
    typed output (JSON/table): `data get <target> <path>` (`/data get`),
    `score <objective> <player>` (`/scoreboard players get`),
    `players`, `pos <selector>`, `blocks/forceload query`, `seed`, etc.
  - Offline mode: when the server is stopped, optionally read `level.dat` /
    `playerdata` via an NBT library for a status snapshot.
- **deploy** — `deploy [--reload]`: run grimmcraft-compiler for the server's
  target, copy the datapack into `world/datapacks/`, and `/reload` via RCON;
  report the compiler diagnostics.
- **logs** — `logs [-f] [--events]`: tail `logs/latest.log`; with `--events`,
  parse chat/join/leave/death/advancement lines into a structured stream.
- **client** (optional) — `client run --version`: launch the game via
  `portablemc`/`minecraft-launcher-lib` using **Microsoft OAuth device-code
  flow**. Never accept a raw password; never store secrets in plaintext; make
  clear the client can't be remote-controlled.

## Config & secrets

- A config file (`grimmcraft.toml` or reuse the compiler's config) for server
  dir, version, flavor, RCON host/port, world name, jar source.
- RCON password and auth tokens: read from env / OS keyring, never committed;
  generate the RCON password on `server install`. Document how it's stored.

## Errors, warnings, UX

- Clear diagnostics: server not running, RCON auth/connection failure (with the
  fix — check `enable-rcon`/password/port), EULA not accepted, version/flavor
  mismatch between server and datapack (reuse compiler diagnostics), Java not
  installed / wrong major version for the MC version.
- Every error says what's wrong, why, and the next step. Non-zero exit codes.
- `--json` output option on read commands for scripting/piping.

## Also generate — tests, examples, docs (in the package)

- **tests/** (pytest, `uv run pytest`, hermetic): unit-test the RCON packet
  encode/decode and the log/`data get` response parsers against captured
  fixtures (no real server). Mock the process manager. Mark any test that needs a
  real server `@pytest.mark.integration` and skip by default.
- **examples/**: a scripted end-to-end (install → start → deploy the Door/Furnace
  example datapack → `rcon` a trigger → `data get` to read the resulting state →
  stop), guarded so it only runs with `--accept-eula` and an explicit opt-in.
- **docs/**: command reference, the RCON/read-data guide (what game state you can
  read and how), the server-vs-client control explanation, config/secrets
  handling, and a troubleshooting page. Match the repo's docs tooling.

## Deliverable checklist

- `python -c "import grimmcraft_cli"` works; `grimmcraft --help` lists commands.
- RCON round-trip works against a real server (documented manual check); parsers
  are unit-tested with fixtures.
- `deploy` produces a datapack that loads and `/reload`s cleanly.
- EULA is never auto-accepted; secrets never printed or committed.
- `uv run pytest` green and hermetic; type-checks clean; style consistent; add
  Taskfile tasks (server up/down, deploy, test) matching existing style.
