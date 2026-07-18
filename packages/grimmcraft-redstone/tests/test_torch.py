"""Redstone torch: inversion and burnout."""

from grimmcraft_core.coordinates import BlockPos, Direction

from grimmcraft_redstone import Circuit, Lever, RedstoneTorch, Simulator
from grimmcraft_redstone.functions.torch import BURNOUT_LIMIT


def test_torch_inverts_its_attachment() -> None:
    circuit = Circuit()
    circuit.add_solid(BlockPos(0, 0, 0))
    torch = circuit.place(RedstoneTorch(BlockPos(0, 1, 0), facing=Direction.UP))
    lever = circuit.place(Lever(BlockPos(1, 0, 0), on=False))  # touches the block
    sim = Simulator(circuit)

    sim.run_until_stable()
    assert torch.output_signal().is_on  # block unpowered -> torch lit

    lever.set(True)
    sim.run_until_stable()
    assert not torch.output_signal().is_on  # block powered -> torch dark


def test_torch_does_not_power_its_own_block() -> None:
    # A lone floor torch on a block must be stable, not a clock.
    circuit = Circuit()
    circuit.add_solid(BlockPos(0, 0, 0))
    circuit.place(RedstoneTorch(BlockPos(0, 1, 0), facing=Direction.UP))
    result = Simulator(circuit).run_until_stable(max_ticks=50)
    assert result.stable
    assert not result.oscillating


class _TogglingContext:
    """A stub context whose attachment power flips every few ticks."""

    tick = 0

    def __init__(self) -> None:
        self.powered = False

    def block_powered(self, pos: BlockPos) -> bool:
        return self.powered


def test_torch_burns_out_under_rapid_toggling() -> None:
    torch = RedstoneTorch(BlockPos(0, 0, 0))
    ctx = _TogglingContext()
    for tick in range(1, 200):
        ctx.powered = (tick // 3) % 2 == 0  # holds each state long enough to flip
        torch.update(ctx, tick)  # type: ignore[arg-type]
        if torch.burned_out:
            break
    assert torch.burned_out
    assert len(torch._flips) > BURNOUT_LIMIT or torch.burned_out
    assert not torch.output_signal().is_on  # burned-out torch is dark
