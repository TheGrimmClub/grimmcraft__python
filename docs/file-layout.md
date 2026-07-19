# The shape of a module

`grimmclub-filesystem/archive.py` is the reference: a trainee opening any club
module should find the same landmarks in the same order. This records what those
landmarks are, so they can be applied deliberately rather than copied by guess.

## The module docstring

One summary line, then the public surface as two lists — what a reader needs
before reading any code:

```python
"""
Zip archives — create and restore, without the macOS ``__MACOSX`` junk.

# Classes:

- `Archive( name, path )`

# Functions:

- `create_archive(from, to, name)`: using `Archive.create()`
- `extract_archive(zip, to)`: using `Archive.extract()`

Prose about the design goes after the lists, not before them.
"""
```

Listing the delegation (`using Archive.create()`) is the useful part: it says the
functions are a convenience layer, not a second implementation.

## The body, in order

```python
# Includes standard      the standard library (or the grimmclub facade)
# Includes external      third-party packages
# Includes internal      this workspace

# Types                  type aliases
# Constants              module constants

# Main Class             the class the module exists for

# Function interface     thin module-level wrappers over that class
```

Omit any section that is empty — an empty `# Constants` heading is noise. Keep
the order even when sections are missing, so the eye learns one shape.

## Inside a class

Group members with a dashed rule naming the group, padded to the line width:

```python
    # --- name ----------------------------------------------------------------
    # --- path ----------------------------------------------------------------
    # --- the archive itself --------------------------------------------------
```

Group by *what the reader is looking for*, not by language mechanics: `# --- name`
covers the property, its setter and its validation together, which is more useful
than separate `# --- properties` and `# --- validation` blocks that force
cross-referencing.

## Where this applies

The club packages — `grimmclub`, `grimmclub-standardlib`, `grimmclub-filesystem`,
`grimmclub-diagnostics`, `grimmclub-mentor` — are teaching material as much as
code, and follow this fully.

The `grimmcraft-*` packages are not converted. There are ~140 such files, and a
marker is only worth adding where a human decided it belongs: a script can label
`# Constants` correctly but cannot tell the main class from a helper, and a
wrongly placed `# Main Class` is worse than none. Convert a module when you next
have reason to work in it.

**Generated modules are exempt.** They carry
`Do not edit by hand; regenerate with _generate/…`, so any marker would have to
be emitted by the generator, and their shape (a docstring, an import, one enum)
has no sections to separate.
