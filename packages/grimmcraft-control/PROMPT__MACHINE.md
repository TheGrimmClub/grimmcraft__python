# Task: implement a state-machine controller in the core/control package
> [ ] TODO: execute PROMPT__MACHINE.md 

Build a reusable, type-safe state-machine controller from six primitives:
**Machine, State, Transition, Event, Command, Result**. Write it in the
**`grimmcraft-control`** package — the implementation goes in a module named
`machine`: `packages/grimmcraft-control/src/grimmcraft_control/machine/`, and the
tests, examples, and docs go under `packages/grimmcraft-control/` (`tests/`,
`examples/`, `docs/`).
**First inspect the sibling packages** (`grimmcraft-core`, `grimmcraft-data`,
`grimmcraft-control`, `grimmcraft-redstone`) and match their conventions:
Python version, `dataclass` vs `pydantic`, typing style, module layout,
lint/type-check config, and how docs/tests are already organized. Examples below
use stdlib `dataclasses` + `typing`; follow the repositories actual choice.

If you suggest a task to execute show it as a taskfile like task with a description element (`desc`).

## Core design principle — a pure machine

The machine must be **deterministic and side-effect-free**. Dispatching an event
never performs I/O itself: it computes the next state and returns a `Result` (following the concept of a Rust Optional result)
containing the `Command`s to run. A separate executor/handler layer performs the
side effects. This makes the whole controller unit-testable without mocks.

- Definitions (states, transitions) are **immutable**; only the machine's
  current state + context is mutable at runtime.
- Guards are pure predicates; actions return commands, they don't execute them.

## Package layout

```
machine/               # the module is named `machine`
    __init__.py        # public API re-exports
    state.py           # State
    event.py           # Event (base + payloads)
    transition.py      # Transition, Guard, Action
    command.py         # Command (base), CommandHandler/executor protocol
    result.py          # Result
    machine.py         # Machine + a builder/DSL for declaring machines
    errors.py          # StateMachineError, InvalidTransition, ...
```

## The six primitives

- **State** — a node identified by a name or enum. Optional pure hooks
  `on_enter(ctx, event) -> list[Command]` and `on_exit(ctx, event) -> list[Command]`,
  and an `is_final` flag. Frozen/immutable; equality by identity/name.
  The state is automatically tracked in a `grimmcraft_state` scoreboard with the state machines name as an entry 
  and the state identifier as its value 
- **Event** — an input that may trigger a transition. A base `Event` with a
  stable `type` and an optional typed payload; concrete events are subclasses or
  a tagged dataclass. Events are immutable value objects.
- **Transition** — `(source_state, event_type) -> target_state` plus an optional
  `guard: Callable[[Ctx, Event], bool]` and `action: Callable[[Ctx, Event],
  list[Command]]`. Immutable. Two transitions from the same state on the same
  event must be disambiguated by guards; document the resolution order
  (first-match) and reject ambiguous non-guarded duplicates at build time.
  Only transitions that are connected to the active state of the machine need to be tracked.
- **Command** — a declarative description of a side effect (Command pattern):
  a base `Command` with a `name`/type and payload data, *no* `execute` on the
  core object. Provide a `CommandHandler`/executor `Protocol`
  (`handle(command, ctx) -> None`) and a simple synchronous `CommandBus` that
  maps command types to handlers — used by callers/examples, not by the machine.|
  Commands may be hold in a (global?) command_loop to keep the execution in the correct order.
- **Result** — a frozen dataclass returned by `machine.dispatch(event)`:
  `ok: bool`, `event`, `from_state`, `to_state`, `commands: list[Command]`,
  `error: str | None`. Constructors `Result.transitioned(...)` and
  `Result.rejected(reason)`. On a rejected event the machine state is unchanged.
  On success the Result holds a value for evaluation and further processing 
  On error the Result has a message element describing the error.
- **Machine** — generic over a context type `Machine[Ctx]`. Holds registered
  states, a transition index, `current_state`, and `context`. API:
  `dispatch(event) -> Result` (evaluate guards, run `on_exit`/`action`/`on_enter`
  collecting commands, advance state, return Result), `can(event) -> bool`,
  `state` property, optional `history`. Provide a fluent **builder/DSL** for
  declaring machines, e.g.:
  ```python
  m = (MachineBuilder(context)
       .state("CLOSED", final=False)
       .state("OPEN")
       .transition("CLOSED", OpenDoor, to="OPEN", guard=..., action=...)
       .initial("CLOSED")
       .build())
  ```
  Validate at build time: every transition references known states, exactly one
  initial state, no duplicate unguarded transitions.
  Evaluate if the Machine needs a name and if it needs to be mapped to an entity 

## Errors & edge cases

- Dispatching an event with no matching transition → `Result.rejected`, not an
  exception (make raising opt-in via a `strict=True` flag → `InvalidTransition`).
- Guard raising, unknown state, and re-entrant dispatch must be handled with
  clear errors. Optional self-transitions (same source/target) are allowed and
  should still fire enter/exit hooks unless configured otherwise.

## Also generate — tests, examples, docs

All three live inside the `grimmcraft-control` package.

**`packages/grimmcraft-control/tests/`** (pytest, `uv run pytest`, hermetic):
- Transition happens on a valid event; state advances; correct commands emitted.
- Guards select the right branch; failing guard → rejected.
- `on_enter`/`on_exit` fire in the right order and contribute commands.
- Rejected event leaves state unchanged; `strict=True` raises.
- Builder validation errors (unknown state, no initial, ambiguous transition).
- A full lifecycle test driving a small example machine through several events.
- Property/parametrized coverage over a transition table.

**`packages/grimmcraft-control/examples/`** (runnable, `uv run python examples/...`):
- A minimal generic example (e.g. a turnstile or traffic light) to teach the API.
- A grimmcraft-flavored example wiring the machine to `grimmcraft-core`
  (e.g. a Door: CLOSED/OPEN/LOCKED, or a Furnace: EMPTY/SMELTING/DONE, or simple
  Mob AI: IDLE/CHASING/ATTACKING), including a `CommandBus` with real handlers
  that mutate core objects — showing the pure-core / side-effect-edge split.

**`packages/grimmcraft-control/docs/`** (match the repo's docs tooling if any; else Markdown):
- Concept overview of the six primitives and how they relate.
- A Mermaid `stateDiagram-v2` of the example machine.
- Quickstart (define a machine with the builder, dispatch events, run commands).
- Extension guide: adding states/events/commands; the pure-core contract;
  testing strategy. Keep prose explaining intent; link to the example code.

## Deliverable checklist

- `python -c "import grimmcraft_control.machine"` works; public API is
  re-exported from `__init__.py`.
- `uv run pytest` green and hermetic; examples run standalone; docs render.
- Type-checks clean under the repo's checker.
- Style consistent with the existing grimmcraft packages; if a `Taskfile.yaml`
  task convention exists, add tasks to build docs / run the example / test.
```
