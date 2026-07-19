"""Runnable examples for every grimmcraft package.

Each module is a standalone program — run it with ``python -m``::

    python -m grimmcraft_examples.tutorial_lamp

They live together rather than beside the packages they demonstrate for one
reason: the interesting examples are *cross-package* (capture a structure,
place it from a machine, compile the pack, decompile it back), and an example
may only honestly import what its package declares. Collecting them here lets
this package depend on everything while each library package's dependencies
stay minimal and truthful.

The datapacks the compiler examples produce are committed under ``generated/``
as reference output, and double as fixtures for the decompiler's round-trip
tests.
"""
