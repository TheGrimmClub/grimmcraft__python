# grimmcraft-npc

Branching NPC dialogue in the shape Ren'Py made familiar, compiled to a Minecraft
datapack — plus full [Taterzens](https://samolego.github.io/Taterzens/) NPC
presets for the body that speaks the lines.

A dialogue is a set of named **scenes**; a scene says lines, runs effects, and
then either offers a **menu**, jumps to another scene, or ends. That is a state
machine, so a dialogue lowers to `grimmcraft-control`'s `Machine` and inherits
the whole pipeline: validation, compilation, the round-trip guarantee, and
decompilation back to readable Python.

See [docs/architecture.md](docs/architecture.md).
