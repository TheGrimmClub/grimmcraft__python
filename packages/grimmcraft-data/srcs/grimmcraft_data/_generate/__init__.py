"""Code-generation scripts for the grimmcraft_data package.

Each module here is a standalone generator run with `uv run` (or plain
`python`).  The `{type_key}.py` scripts emit the core Enum modules; the
`advanced_{name}.py` scripts download richer datasets, bundle the source JSON
under ``../data/{version}/`` and emit typed accessor modules next to the package
root.  Nothing in this package is imported at runtime by library callers.
"""
