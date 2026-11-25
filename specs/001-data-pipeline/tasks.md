---
description: "Task list for Flight Data Pipeline (Phase 1)"
---

# Tasks: Flight Data Pipeline (Phase 1)

**Input**: Design documents from `/specs/001-data-pipeline/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required by constitution principle II (test-first). In every story, write the test
tasks first and see them fail before the implementation tasks.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story from spec.md (US1–US4)

---

## Phase 1: Setup

- [ ] T001 Add `airportsdata` to dependencies in pyproject.toml and run `uv sync` (lock in uv.lock)
- [ ] T002 [P] Create `config/data.yaml` with carrier, week_start, buffer_days=3, block_minutes range 20–480, elapsed_tolerance=5, base rule (max 3, share ≥ 0.5), candidate carriers [F9, NK]
- [ ] T003 [P] Create test package `tests/data/__init__.py` and `tests/fixtures/` folder

---

## Phase 2: Foundational (blocks all stories)

- [ ] T004 [P] Write tests for config loading and validation (missing keys, bad week date) in tests/data/test_config.py
- [ ] T005 Implement `DataConfig` loader in crewopt/data/config.py
- [ ] T006 [P] Write tests for airport reference (DEN, MCO, HNL, SJU tz; unknown code → None) in tests/data/test_airports.py
- [ ] T007 Implement airport reference from airportsdata in crewopt/data/airports.py
- [ ] T008 [P] Write tests for hhmm parsing ("905", "0", "2400", invalid "1260") in tests/data/test_timeconv.py
- [ ] T009 [P] Write tests for local→UTC conversion and arrival inference (same-day, midnight crossing DEN→MCO, eastbound/westbound, HNL, DST-change date, nonexistent local time) in tests/data/test_timeconv.py
- [ ] T010 Implement hhmm parsing, local→UTC conversion and arrival date inference in crewopt/data/timeconv.py
- [ ] T011 [P] Create synthetic raw fixture covering all edge cases (≈50 rows, BTS column names) in tests/fixtures/bts_sample.csv
- [ ] T012 [P] Write tests for reading only required columns from csv and zip in tests/data/test_bts.py
- [ ] T013 Implement raw reader (csv or zip, required columns, dtypes) in crewopt/data/bts.py

**Checkpoint**: config, airports, time conversion and raw reading are tested and green.

---

## Phase 3: User Story 1 — Clean weekly flight schedule (P1) 🎯 MVP

**Goal**: One clean, UTC-normalized weekly flight table for one carrier with flagged buffer days.
**Independent Test**: Build from the fixture; check row counts, UTC times, buffer flags and a hand-checked sample.

### Tests (write first)
- [ ] T014 [P] [US1] Tests for carrier/window filtering, cancelled/diverted exclusion with counts, buffer flag in tests/data/test_clean.py
- [ ] T015 [P] [US1] Tests for flight_id format, uniqueness and exact-duplicate removal in tests/data/test_clean.py
- [ ] T016 [P] [US1] Test: unknown-time-zone airport → flight excluded and counted in tests/data/test_clean.py
- [ ] T017 [P] [US1] Integration test: build on fixture produces parquet + meta with schema from data-model.md in tests/data/test_pipeline.py
- [ ] T018 [P] [US1] Determinism test: two builds → equal data_sha256 (SC-004) in tests/data/test_pipeline.py

### Implementation
- [ ] T019 [US1] Implement cleaning steps (filter, exclusions with reasons, tz attach, UTC, ids, dedupe, buffer flag, sort) in crewopt/data/clean.py
- [ ] T020 [US1] Implement canonical data checksum and metadata assembly in crewopt/data/pipeline.py
- [ ] T021 [US1] Implement output writing (parquet + meta.json) in crewopt/data/pipeline.py
- [ ] T022 [US1] Implement CLI `build` in crewopt/data/__main__.py per contracts/cli.md

**Checkpoint**: `build` on the fixture produces a correct, deterministic flight table.

---

## Phase 4: User Story 2 — Data quality validation (P2)

**Goal**: Validation report with blocking and warning checks; dataset marked valid/not valid.
**Independent Test**: Seeded-defect fixture → every defect detected.

### Tests (write first)
- [ ] T023 [P] [US2] Create seeded-defect fixture (arrival before departure, wrong tz, duplicate, missing tz, block time 2 min) in tests/fixtures/bts_defects.csv
- [ ] T024 [P] [US2] Tests for blocking checks FR-013–016 in tests/data/test_validate.py
- [ ] T025 [P] [US2] Tests for warning checks FR-017–020 (tail continuity, tail overlap, elapsed consistency, missing tail) in tests/data/test_validate.py
- [ ] T026 [P] [US2] Integration test: defects fixture → `valid: false`, exit code 2 (SC-003) in tests/data/test_pipeline.py

### Implementation
- [ ] T027 [US2] Implement ValidationReport and all checks in crewopt/data/validate.py
- [ ] T028 [US2] Wire validation into pipeline, write validation.json, set exit codes in crewopt/data/pipeline.py and crewopt/data/__main__.py

**Checkpoint**: Bad data can no longer pass silently.

---

## Phase 5: User Story 3 — Network exploration (P3)

**Goal**: Exploration summary and crew-base proposal.
**Independent Test**: Summary totals match dataset row counts.

- [ ] T029 [P] [US3] Tests for summary totals, base-proposal rule, one-tail daily rotation in tests/data/test_explore.py
- [ ] T030 [US3] Implement exploration summary and base proposal in crewopt/data/explore.py
- [ ] T031 [US3] Write summary.md from pipeline in crewopt/data/pipeline.py

---

## Phase 6: User Story 4 — Carrier comparison (P3)

**Goal**: Evidence-based carrier choice.
**Independent Test**: Comparison on fixture lists each candidate with weekly flights, airports, tails.

- [ ] T032 [P] [US4] Tests for carrier comparison table in tests/data/test_explore.py
- [ ] T033 [US4] Implement carrier comparison in crewopt/data/explore.py
- [ ] T034 [US4] Implement CLI `compare-carriers` in crewopt/data/__main__.py
- [ ] T035 [US4] Implement CLI `fetch` with manual-download fallback message in crewopt/data/bts.py and crewopt/data/__main__.py

---

## Phase 7: Real data & polish

- [ ] T036 Download one BTS month (manual if fetch is blocked) into data/raw/bts/ per data/README.md
- [ ] T037 Run compare-carriers, choose carrier + week, record reason in config/data.yaml
- [ ] T038 Run build on real data; all blocking checks pass; review summary (SC-001, SC-005, SC-006)
- [ ] T039 Hand-check ≥10 flights incl. 2 midnight crossings and 1 HNL/SJU flight (SC-002); record in specs/001-data-pipeline/verification.md
- [ ] T040 [P] Update data/README.md with exact commands (SC-007)
- [ ] T041 Run quickstart.md end to end; `uv run pytest` and `ruff` clean

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 → US2 → (US3 ∥ US4) → Phase 7
- US2 depends on US1's pipeline; US3 and US4 depend only on US1's flight table and can run in parallel.
- Within each story: tests first (must fail), then implementation.

## MVP

Phases 1–3 (T001–T022): a correct, deterministic weekly flight table. Stop and validate there
before continuing.
