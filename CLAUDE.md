# CLAUDE.md

Guidance for Claude Code in this repository. Read it at the start of every session.

## Project
Airline **crew pairing** optimization with **hybrid column generation (CG) + machine learning (ML)**.
A learning and interview-preparation project for an Operations Research software role.
- Principles (must follow): `.specify/memory/constitution.md`
- Feature specs, plans and tasks: `specs/NNN-name/`

## Commands
```bash
uv sync                              # install / update dependencies
uv run pytest                        # all tests (must be green before done/commit)
uv run pytest tests/test_x.py -k y   # single test
uv run ruff check --fix . && uv run ruff format .
uv run jupyter lab                   # notebooks/
```

## Layout
```
crewopt/data/        load + clean BTS and airports (all times → UTC)
crewopt/domain/      Flight, Connection, Duty, Pairing, rule classes, cost model
crewopt/network/     flight connection graph
crewopt/solvers/     enumeration (reference), master LP/MIP, pricing (RCSP), column generation
crewopt/ml/          features, training, connection scorer
crewopt/experiments/ baseline vs hybrid comparisons
crewopt/service/     (phase 8) job API, worker
config/rules.yaml    ALL rule parameters and cost weights
specs/               Spec Kit feature specs (one per phase)
data/raw, data/processed   not committed — see data/README.md
```

## Workflow (Spec-Driven Development)
1. One feature per phase: `/speckit-specify` → `/speckit-clarify` (optional) → `/speckit-plan`
   → `/speckit-tasks` → `/speckit-analyze` (optional) → `/speckit-implement`.
2. Use plan mode before multi-file changes.
3. Test first: write the failing test, then the code.
4. Start on a tiny instance (≈10 flights), then scale.
5. When a task is done: tests green, ruff clean, task checked in `tasks.md`, commit.

## Hooks (already configured in .claude/settings.json)
- After every Edit/Write of a `.py` file: ruff fix + format.
- Before finishing a turn: `pytest`; failing tests block finishing. Fix them, never delete or
  weaken a test to make it pass.

## Rules that matter here
- **No magic numbers**: connection times, duty/rest limits, cost weights come from
  `config/rules.yaml`.
- **UTC everywhere** internally. BTS times are local; convert with the airport time zone.
  Handle flights crossing midnight.
- **Use scheduled times**, not actual times, for planning. Drop cancelled and diverted flights.
- **Validate solver output independently**: re-check coverage, re-run rules on chosen pairings,
  recompute cost. Assert LP ≤ MIP (minimization).
- **ML never decides legality**; hybrid runs always end with a full-network pricing check.
- **Reproducibility**: fixed seeds; log dataset id, config hash, solver/model versions.
- ML train/test split by day/week, never by row.
- Solver access goes through Pyomo (`SolverFactory("appsi_highs")`) so the solver stays swappable.

## Gotchas
- Pyomo duals need `model.dual = Suffix(direction=Suffix.IMPORT)` before solving the LP.
- Set partitioning master can be infeasible early in CG: keep high-cost artificial columns.
- Do not commit anything under `data/` except `data/README.md`, nor the PDFs in `papers/`.
- When you introduce an OR/ML concept, explain it in one or two plain sentences.
