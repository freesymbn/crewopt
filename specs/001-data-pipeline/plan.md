# Implementation Plan: Flight Data Pipeline (Phase 1)

**Branch**: `001-data-pipeline` | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-data-pipeline/spec.md`

## Summary

Turn one raw BTS On-Time Performance month file into a validated, UTC-normalized weekly flight
table for one carrier (plus 3 flagged buffer days), with metadata, a validation report, an
exploration summary and a carrier comparison. Implemented as a small Python package
(`crewopt.data`) with a command-line entry point; pure functions per step so every edge case
(midnight crossing, "2400", DST, non-contiguous U.S.) is unit-tested on tiny fixtures.
Time zones come from the `airportsdata` package (IATA → IANA tz); conversion uses Python's
`zoneinfo`. Arrival times are derived from local arrival time + date inference and then
cross-checked against the scheduled elapsed time, so the two sources validate each other.

## Technical Context

**Language/Version**: Python 3.12 (managed with uv)

**Primary Dependencies**: pandas, pyarrow (Parquet), airportsdata (airport → IANA time zone),
zoneinfo (stdlib), pyyaml; pytest for tests

**Storage**: Files — raw zip/csv in `data/raw/bts/`, outputs in `data/processed/`
(Parquet + JSON metadata + JSON validation report + Markdown summary)

**Testing**: pytest; unit tests on hand-written fixtures in `tests/fixtures/`, one integration
test on a ~50-row synthetic raw file, determinism test (checksum equality)

**Target Platform**: macOS / Linux laptop

**Project Type**: Python library + CLI (`python -m crewopt.data ...`)

**Performance Goals**: Weekly dataset from a downloaded month file in < 2 min (SC-006). A month
is ~600k rows for all carriers; reading only the needed columns and filtering by carrier early
keeps this well under the target.

**Constraints**: Deterministic output (FR-012); no rule numbers hard-coded (constitution III);
automated download may be blocked → manual path documented (FR-002)

**Scale/Scope**: One carrier, one week + 3 days ≈ 3–5k flights, ~60–100 airports, ~150–300 tails

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan complies | Status |
|---|---|---|
| I. Correctness before speed | Blocking checks FR-013–016 gate dataset validity; arrival time derived two ways and cross-checked (FR-019); hand-check of ≥10 flights (SC-002) | ✅ |
| II. Test-first | Every parser/converter/check gets a failing test first; seeded-defect fixture (SC-003) | ✅ |
| III. Rules are data | Carrier, week, buffer days, block range, tolerance, base rule in `config/data.yaml` | ✅ |
| IV. Safety constraints hard | N/A for this phase (no crew rules yet); unknown time zones are never guessed | ✅ |
| V. Reproducibility | Stable flight ids, deterministic sort, data checksum + source checksum + config hash in metadata | ✅ |
| VI. Observability | Run summary with counts per exclusion reason; JSON validation report; structured logging | ✅ |
| VII. Simplicity | Plain pandas, no database, no orchestration framework | ✅ |
| Ethics | N/A (public flight data only) | ✅ |

Re-check after design: ✅ no violations, no complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-data-pipeline/
├── spec.md
├── plan.md              # this file
├── research.md          # decisions and alternatives
├── data-model.md        # Flight, Airport, Dataset, ValidationReport
├── quickstart.md        # how to run and verify
├── contracts/
│   ├── cli.md           # command-line interface
│   └── outputs.md       # output files and schemas
└── checklists/requirements.md
```

### Source Code (repository root)

```text
config/
└── data.yaml                 # carrier, week, buffer days, thresholds, candidates

crewopt/data/
├── __init__.py
├── __main__.py               # CLI: fetch | compare-carriers | build
├── config.py                 # DataConfig (load + validate config/data.yaml)
├── bts.py                    # locate/fetch raw month file, read needed columns
├── airports.py               # airport reference with IANA tz (airportsdata)
├── timeconv.py               # hhmm parsing, "2400", local→UTC, arrival date inference
├── clean.py                  # filter carrier/window, drop cancelled/diverted, ids, flags
├── validate.py               # blocking + warning checks → ValidationReport
├── explore.py                # exploration summary, base proposal, carrier comparison
└── pipeline.py               # orchestration, writing outputs + metadata

tests/
├── fixtures/
│   ├── bts_sample.csv        # ~50 rows, synthetic, covers every edge case
│   └── bts_defects.csv       # seeded defects for SC-003
└── data/
    ├── test_timeconv.py
    ├── test_clean.py
    ├── test_validate.py
    ├── test_explore.py
    └── test_pipeline.py      # integration + determinism
```

**Structure Decision**: Single Python package (`crewopt`), this feature lives in
`crewopt/data/`. Tests mirror the package under `tests/data/`.

## Complexity Tracking

No violations.
