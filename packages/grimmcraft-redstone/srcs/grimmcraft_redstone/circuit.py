"""The :class:`Circuit` — a spatial graph of placed redstone components.

Components are keyed by their integer :class:`~grimmcraft_core.coordinates.BlockPos`
(each cell holds at most one).  Neighbours are resolved on demand by
:class:`~grimmcraft_core.coordinates.Direction`, so the "graph" is implicit in the
world grid, exactly like Minecraft: adjacency *is* connectivity.  Full solid
blocks (which conduct and give torches something to attach to) are tracked too.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TypeVar

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block
from grimmcraft_redstone.component import RedstoneComponent

#: `place` hands back exactly what it was given, so it is generic over the
#: component type — otherwise `circuit.place(Lever(...))` would come back typed
#: as the base class and every concrete method (`lever.flip()`) would be lost.
AnyComponent = TypeVar("AnyComponent", bound=RedstoneComponent)


class Circuit:
    """A grid of placed :class:`RedstoneComponent`s plus solid conductor blocks."""

    def __init__(self) -> None:
        self._components: dict[BlockPos, RedstoneComponent] = {}
        self._solids: dict[BlockPos, Block] = {}

    # -- building -------------------------------------------------------------
    def place(self, component: AnyComponent) -> AnyComponent:
        """Place ``component`` at its own ``position`` and return it.

        Raises :class:`ValueError` if the cell is already occupied (remove first).
        """
        pos = component.position
        if pos in self._components:
            raise ValueError(f"cell {pos} already holds {self._components[pos].name}")
        self._components[pos] = component
        if component.IS_SOLID:
            self._solids[pos] = component.block_type
        return component

    def add_solid(self, pos: BlockPos, block: Block = Block.STONE) -> None:
        """Mark ``pos`` as a full solid block (conducts power, holds torches)."""
        self._solids[pos] = block

    def remove(self, pos: BlockPos) -> RedstoneComponent | None:
        """Remove and return whatever component is at ``pos`` (also clears solids)."""
        self._solids.pop(pos, None)
        return self._components.pop(pos, None)

    def connect(self, a: BlockPos, b: BlockPos) -> None:
        """Assert ``a`` and ``b`` are wired neighbours (validates adjacency).

        Connectivity in a grid is positional, so this is a checked no-op used to
        document intent and catch mistakes: it raises if the cells are not
        face-adjacent.
        """
        if b not in a.neighbors():
            raise ValueError(f"{a} and {b} are not face-adjacent; cannot connect")

    # -- queries --------------------------------------------------------------
    def get(self, pos: BlockPos) -> RedstoneComponent | None:
        """The component at ``pos``, or ``None``."""
        return self._components.get(pos)

    def component_at(self, pos: BlockPos) -> RedstoneComponent | None:
        """Alias of :meth:`get` (matches the :class:`SimContext` vocabulary)."""
        return self._components.get(pos)

    def is_solid(self, pos: BlockPos) -> bool:
        """Whether ``pos`` holds a full solid block (placed solid or solid component)."""
        return pos in self._solids

    def neighbors(self, pos: BlockPos) -> dict[Direction, RedstoneComponent]:
        """The components face-adjacent to ``pos``, keyed by the :class:`Direction`."""
        found: dict[Direction, RedstoneComponent] = {}
        for direction in Direction:
            neighbor = self._components.get(pos.step(direction))
            if neighbor is not None:
                found[direction] = neighbor
        return found

    def neighbor(self, pos: BlockPos, direction: Direction) -> RedstoneComponent | None:
        """The component one step from ``pos`` toward ``direction`` (or ``None``)."""
        return self._components.get(pos.step(direction))

    def items(self) -> Iterator[tuple[BlockPos, RedstoneComponent]]:
        """Iterate ``(pos, component)`` pairs in deterministic position order."""
        for pos in sorted(self._components, key=lambda p: (p.x, p.y, p.z)):
            yield pos, self._components[pos]

    def components(self) -> list[RedstoneComponent]:
        """All placed components, in deterministic position order."""
        return [c for _, c in self.items()]

    def positions(self) -> list[BlockPos]:
        """All occupied positions, in deterministic order."""
        return [p for p, _ in self.items()]

    def reset(self) -> None:
        """Reset every component to its powered-off state (keeps the layout)."""
        for component in self._components.values():
            component.reset()

    def __contains__(self, pos: object) -> bool:
        return pos in self._components

    def __len__(self) -> int:
        return len(self._components)

    def __iter__(self) -> Iterator[RedstoneComponent]:
        return iter(self.components())
