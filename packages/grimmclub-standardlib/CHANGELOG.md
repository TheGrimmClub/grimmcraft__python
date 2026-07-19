# Changelog — grimmclub-standardlib

## feat(yaml): a YAML facade, and honest Path aliases — 2026-07-19

`yaml` joins `json` with the same four calls, so a lesson that reads one reads
the other the same way. Two deliberate departures from PyYAML:

- **`load` means `safe_load`.** PyYAML's `load` can construct arbitrary Python
  objects, so reading an untrusted file can run code. Not a default to hand to
  someone learning the language. `unsafe_load` exists, named so that choosing it
  is visible in the code that chose it.
- **`dump` keeps key order.** PyYAML sorts alphabetically, which scrambles a
  hand-written config the first time a program rewrites it. `config.py` had
  already been passing `sort_keys=False` by hand — now it is the default.

**PyYAML is imported lazily**, so `dependencies = []` still holds and every
package can keep depending on this one freely. A test asserts that. `grimmclub`,
the front door, declares PyYAML itself, so trainees always have it.

### fix(path): the explicit names had turned the logging off

`open` and `mkdir` had been renamed to `open_file` and `make_directory`. On a
`pathlib.Path` subclass a rename does not rename anything — it stops overriding.
Both original names still existed, inherited, and silently logged nothing: the
two operations students perform most were the two missing from the trace. It is
load-bearing internally too, since `write_text` goes through `self.open()` and
`mkdir(parents=True)` recurses through `self.mkdir()`.

So the house names are now **aliases**: `open_file`, `create_directory`,
`remove_file`, `remove_directory`. Both spellings log.

`rmdir` also gained the override it was missing — `mkdir` was logged and its
opposite was not.


## feat(standardlib): split out of grimmclub as the bottom of the stack

The standard-library facade, the logging helpers (`log`, `debug`, `banner`,
`set_debug`) and the house vocabulary (`yes`/`no`/`true`/`false`/`on`/`off`)
moved here from `grimmclub`, along with the logging `Path` and `json` wrappers.

`grimmclub` had been doing two jobs: it was the front door trainees import
*and* the shared vocabulary every other package needs. Those pull in opposite
directions — a front door belongs on top, shared vocabulary at the bottom —
which is why the layering was ambiguous and why `grimmclub-filesystem` had
quietly grown its own second definition of `yes`/`no`/`true`/`false`/`Any`.

Splitting the roles resolves it:

    grimmclub                 front door: re-exports everything below
      ├── grimmclub-standardlib   (this package) — no dependencies, ever
      └── grimmclub-filesystem    depends on standardlib

There is now exactly one `yes` in the workspace. A test asserts this package
imports nothing of ours, since that is the property the whole arrangement rests
on: if it ever fails, the layering has inverted.
