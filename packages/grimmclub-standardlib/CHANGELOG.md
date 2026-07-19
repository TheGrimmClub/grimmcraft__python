# Changelog — grimmclub-standardlib

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
