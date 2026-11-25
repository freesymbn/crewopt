# Crewopt Constitution

Crew pairing optimization with hybrid column generation and machine learning.
This document holds the non-negotiable principles of the project. Specs, plans, tasks and code
must comply with it.

## Core Principles

### I. Correctness Before Speed (NON-NEGOTIABLE)
- Every phase has explicit validation checks; the next phase starts only after they pass.
- Optimization errors are silent: wrong data still produces an "optimal" solution. Therefore
  every solver result is re-validated independently: each flight covered exactly as required,
  every pairing re-checked by the rule engine, cost recomputed outside the solver.
- Mathematical invariants are asserted in code and tests (e.g. LP relaxation value ≤ MIP value
  for minimization; master LP objective never increases across column generation iterations).
- A small instance with a known optimal solution (exhaustive enumeration) is the reference
  against which column generation and the hybrid method are tested.

### II. Test-First (NON-NEGOTIABLE)
- Tests are written before implementation and must fail first (Red → Green → Refactor).
- Every rule has at least one passing and one failing example.
- `uv run pytest` must be green before a task is marked done and before every commit.

### III. Rules Are Data, Not Code
- Regulatory and company parameters (connection times, duty limits, rest, pairing length,
  cost weights) live in `config/rules.yaml`. No such number is hard-coded in solver logic.
- Each rule is a separate class behind a common interface; adding or changing a rule must not
  require changes to the optimization algorithms.

### IV. Safety Constraints Are Hard Constraints
- Duty time, rest and flight-time limits are hard constraints: no cost trade-off may violate them.
- Machine learning may only speed up the search (prune the network, warm-start the master).
  It never decides legality and never replaces the solver.
- Every hybrid run ends with a full-network pricing check (the "safety net") so ML errors
  cannot silently degrade solution quality.

### V. Reproducibility
- Same input + same config + same seed → same result.
- Every run records: input dataset id, config hash, solver and model versions, random seed.
- Raw and processed data are never committed; `data/README.md` documents how to recreate them.
- ML models are versioned; each optimization result references the model version it used.

### VI. Observability
- Structured (JSON) logs; every log line of a job carries its job id.
- Column generation logs per iteration: master LP value, columns added, pricing time.
- Results report KPIs: total cost, number of pairings, duty days, hotel nights, deadheads,
  time away from base, lower bound, upper bound and optimality gap.

### VII. Simplicity and Learnability
- Start with the simplest correct approach; add complexity only with a measured reason.
- Code and docs explain *why*, not only *what*. Decisions and their alternatives are recorded in
  each feature's `research.md`.
- Small steps: start every feature on a tiny instance (≈10 flights) before scaling up.

## Ethical Boundaries

- The system supports human planners; it does not replace them. Final decisions stay with people.
- Objectives that aim to cut crew jobs or erode crew working conditions are out of scope.
- Crew quality of life is a first-class objective: time away from base and hotel nights are part
  of the cost model and reported in every result.
- If a requested feature conflicts with these boundaries, stop and raise it before implementing.

## Technical Constraints

- Language: Python ≥ 3.12, managed with `uv`. Package: `crewopt/`.
- Optimization: Pyomo modeling layer, HiGHS solver (open source). Solver must stay swappable.
- ML: scikit-learn and LightGBM. Train/test splits by day/week, never by row (avoid leakage).
- Data: BTS On-Time Performance (scheduled times), OurAirports (time zones). All times in UTC
  internally.
- Code, comments, specs, commit messages: English. Learning notes may be Turkish.
- Lint/format: ruff. Tests: pytest.

## Development Workflow

- Spec-Driven Development with Spec Kit, one feature per project phase:
  `/speckit-specify` → (`/speckit-clarify`) → `/speckit-plan` → `/speckit-tasks` →
  (`/speckit-analyze`) → `/speckit-implement`.
- Definition of Done for a task: tests written first and green, ruff clean, acceptance criteria
  of the spec met, validation checks of the phase pass, task checked in `tasks.md`, committed with
  a meaningful message.
- Use plan mode before multi-file changes. Review changes before accepting them.

## Governance

- This constitution supersedes other practices. Specs and plans must state how they comply.
- Amendments: write the change and its reason, bump the version, update the date, and check
  dependent docs (`CLAUDE.md`, specs) for consistency.
- Versioning: MAJOR = principle removed or redefined; MINOR = principle or section added;
  PATCH = clarification.
- Runtime guidance for the coding agent lives in `CLAUDE.md`.

**Version**: 1.0.1 | **Ratified**: 2026-11-24 | **Last Amended**: 2026-11-25
