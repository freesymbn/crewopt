# Feature Specification: Flight Data Pipeline (Phase 1)

**Feature Branch**: `001-data-pipeline`

**Created**: 2026-11-25

**Status**: Implemented (verified 2026-11-25, see verification.md)

**Input**: User description: "Phase 1 - Data: download, explore and clean one week of BTS flights for a single A320-family carrier, convert all times to UTC, and produce a validated dataset"

## Context

Every later phase (rule engine, flight network, column generation, ML) consumes the flight list
produced here. In a real airline this list comes from the flight information system. Optimization
errors caused by bad data are silent: a wrong time zone still yields an "optimal" but meaningless
crew plan. This phase therefore puts correctness and traceability first (constitution principles
I and V).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Produce a clean weekly flight schedule (Priority: P1)

As the planner/developer, I select a carrier and a week, and I get one clean table of that
carrier's **scheduled** flights for the week: every flight with origin, destination, scheduled
departure and arrival **in UTC**, block time, flight number and tail number. Cancelled and diverted
flights are excluded. A short buffer of following days is included and marked, so that pairings
starting late in the week can be completed in later phases.

**Why this priority**: Nothing else in the project can start without this table. It is the MVP of
this phase.

**Independent Test**: Run the pipeline on one downloaded month file for one carrier and one week;
inspect the output table: row count, time zones, a hand-checked sample of flights.

**Acceptance Scenarios**:

1. **Given** a raw monthly BTS file and an airport reference file, **When** the pipeline is run
   for carrier C and week W, **Then** the output contains only carrier C's flights whose scheduled
   departure falls in week W or in the buffer days, with every buffer flight flagged.
2. **Given** a flight departing Denver at 22:30 local time and arriving in Orlando after midnight
   local time, **When** it is converted, **Then** its UTC departure and arrival are correct and the
   arrival is on the next calendar day.
3. **Given** a raw record marked cancelled or diverted, **When** the pipeline runs, **Then** that
   record is absent from the output and counted in the run summary.
4. **Given** the same inputs and the same configuration, **When** the pipeline is run twice,
   **Then** the two outputs are identical.

---

### User Story 2 - Validate data quality before anyone uses it (Priority: P2)

As the planner/developer, I get a validation report for every produced dataset that states which
quality checks passed or failed, with counts and examples of offending rows, so I never build on
broken data unknowingly.

**Why this priority**: Implements constitution principle I ("correctness before speed"). Without
it, errors surface only phases later, where they are much harder to trace.

**Independent Test**: Run the checks against a deliberately corrupted small sample (wrong time
zone, arrival before departure, duplicate row) and confirm each defect is detected and reported.

**Acceptance Scenarios**:

1. **Given** a dataset where one flight's arrival is before its departure, **When** validation
   runs, **Then** the check fails, the flight is listed, and the dataset is marked as not valid.
2. **Given** a flight whose origin airport has no known time zone, **When** the pipeline runs,
   **Then** that flight is excluded, listed in the report, and the run summary shows the count.
3. **Given** a clean dataset, **When** validation runs, **Then** all blocking checks pass and the
   dataset is marked valid.

---

### User Story 3 - Understand the carrier's network (Priority: P3)

As the planner/developer, I get an exploration summary of the selected week: flights per day,
busiest airports, block-time distribution, number of aircraft (tail numbers) and a typical
aircraft's daily rotation. From it I choose the crew bases for later phases.

**Why this priority**: Needed to make informed choices (crew bases, problem size) and to learn the
domain, but the pipeline is usable without it.

**Independent Test**: Generate the summary for the produced dataset and check that the totals
match the dataset's row counts.

**Acceptance Scenarios**:

1. **Given** a valid dataset, **When** the exploration summary is generated, **Then** it lists
   the top departure airports with their share of departures and proposes crew-base candidates
   by a documented rule.
2. **Given** a valid dataset, **When** I look up one tail number, **Then** I see its flights in
   time order for one day, forming a connected sequence (arrival airport = next departure airport)
   unless a gap is reported.

---

### User Story 4 - Choose the carrier with evidence (Priority: P3)

As the planner/developer, I compare candidate A320-family carriers in the raw month (flights per
week, number of airports, number of aircraft) and record which carrier was chosen and why.

**Why this priority**: The carrier choice shapes problem size. It is a one-time decision, so a
simple comparison is enough.

**Independent Test**: Run the comparison on the raw month and confirm the chosen carrier and the
reason are recorded with the dataset.

**Acceptance Scenarios**:

1. **Given** a raw month file, **When** the comparison is run for the candidate carriers,
   **Then** a table with weekly flights, airports and aircraft per carrier is produced, and the
   selected carrier and reason are recorded in the dataset metadata.

---

### Edge Cases

- **Midnight crossing**: local arrival time earlier than local departure time means next-day
  arrival; must be resolved before UTC conversion.
- **"2400" times** in the raw data: treated as 00:00 of the following day.
- **Times without leading zeros** (e.g. "905" meaning 09:05) are parsed correctly.
- **Daylight saving time changes** inside the selected week: conversion must still be correct
  (week selection prefers weeks without a change, but conversion must not depend on that).
- **Airports outside the contiguous U.S.** (e.g. Hawaii, Puerto Rico) with time zones that do not
  observe DST.
- **Missing tail number**: flight is kept (crew needs it covered) but flagged; continuity checks
  skip it.
- **Duplicate records** (same carrier, flight number, date, origin): detected and reported;
  exact duplicates are removed.
- **Inconsistent block time**: scheduled elapsed time disagrees with the UTC arrival−departure
  difference by more than a tolerance → flagged in the report.
- **Airport missing from the time-zone reference** → flight excluded and reported (never guessed).
- **Empty result** (carrier has no flights in the week) → run fails with a clear message.

## Requirements *(mandatory)*

### Functional Requirements

**Input**

- **FR-001**: The pipeline MUST read a raw monthly BTS On-Time Performance file that the user has
  placed in the project's raw-data folder.
- **FR-002**: The pipeline SHOULD be able to fetch a given year/month file automatically; when the
  download is not possible, it MUST tell the user exactly which file to download manually and where
  to put it.
- **FR-003**: The pipeline MUST use an airport reference that provides, for every airport code in
  the selected data, its IANA time zone and coordinates.

**Selection and cleaning**

- **FR-004**: Users MUST be able to choose the carrier, the week (by its Monday date) and the number
  of buffer days (default: 3, matching the 4-day maximum pairing length) through configuration,
  without code changes.
- **FR-005**: The pipeline MUST use **scheduled** departure/arrival times and scheduled elapsed time;
  actual times MUST NOT be used.
- **FR-006**: The pipeline MUST exclude cancelled and diverted flights and count them in the run
  summary.
- **FR-007**: The pipeline MUST convert every departure and arrival to UTC using the airport's time
  zone on that date, handling midnight crossing, "2400" values and DST.
- **FR-008**: The pipeline MUST assign each flight a unique, stable identifier that is the same on
  every run with the same inputs.
- **FR-009**: The pipeline MUST flag buffer-day flights so later phases can treat them differently.

**Output and traceability**

- **FR-010**: The pipeline MUST write the cleaned flights to a single file in the processed-data
  folder, named by carrier and week, with rows in a deterministic order.
- **FR-011**: Each output MUST have metadata: source file name and checksum, carrier, week, buffer
  days, configuration used, run time, row counts (raw, excluded by reason, final), and the carrier
  selection reason.
- **FR-012**: Re-running with identical inputs and configuration MUST produce byte-identical
  flight data.

**Validation (blocking checks — a dataset failing any is marked not valid)**

- **FR-013**: Every flight's UTC arrival MUST be after its UTC departure.
- **FR-014**: Every flight's block time MUST be within a configured range (default 20 min – 8 h).
- **FR-015**: Every flight MUST have origin ≠ destination and both airports MUST have a time zone.
- **FR-016**: Flight identifiers MUST be unique.

**Validation (reported checks — warnings with counts and examples)**

- **FR-017**: Tail continuity: share of consecutive same-tail flights where arrival airport equals
  next departure airport, and list of breaks.
- **FR-018**: Aircraft overlap: same tail number scheduled on two flights at the same time.
- **FR-019**: Block-time consistency between scheduled elapsed time and UTC difference
  (tolerance configurable, default 5 min).
- **FR-020**: Flights with missing tail numbers.

**Exploration**

- **FR-021**: The pipeline MUST produce an exploration summary (flights per day, top airports,
  block-time distribution, number of aircraft, example daily rotation of one aircraft).
- **FR-022**: The summary MUST propose crew-base candidates using a documented rule (default: the
  airports with the most departures that together cover at least half of all departures, at most 3).
- **FR-023**: The pipeline MUST produce a carrier comparison for a configurable list of candidate
  carriers (default: Frontier Airlines and Spirit Airlines, both A320-family operators).

### Key Entities

- **Flight (leg)**: One scheduled, non-stop flight. Attributes: identifier, carrier, flight number,
  tail number (may be missing), origin, destination, scheduled departure (UTC and local),
  scheduled arrival (UTC and local), block time, distance, is-buffer flag.
- **Airport**: Code, name, coordinates, IANA time zone.
- **Dataset**: One produced weekly flight table and its metadata (see FR-011) and validation
  report.
- **Validation report**: List of checks with status (pass / fail / warning), counts and example
  rows; overall validity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of flights in a valid dataset have UTC departure and arrival times, and 0
  flights arrive before they depart.
- **SC-002**: A hand-checked sample of at least 10 flights (including at least 2 midnight-crossing
  and 1 non-contiguous-U.S. flight) matches published local schedules after converting back from
  UTC.
- **SC-003**: Every seeded defect in a corrupted test sample (wrong time zone, arrival before
  departure, duplicate, missing time zone) is detected by validation.
- **SC-004**: Two runs with identical inputs produce identical flight data (checksum equal).
- **SC-005**: Tail continuity is at least 95% for the selected week, or the report explains why
  it is lower.
- **SC-006**: Producing a weekly dataset from an already downloaded month file takes less than
  2 minutes on a laptop.
- **SC-007**: Someone new to the project can produce the dataset by following the data guide
  alone, without asking questions.

## Assumptions

- The project uses U.S. data because airline crew data is not public and BTS flight data is free
  and detailed (tail numbers, scheduled times). The domain logic is the same as for any carrier.
- A320-family-only carriers are preferred so that one cockpit crew type can fly every flight
  (similar to the Turkish Airlines A320 study). Final choice is made from evidence (US 4).
- The week is a Monday–Sunday week of the most recent month available from BTS, preferably
  without U.S. federal holidays and without a DST change.
- Buffer days default to 3 because pairings last at most 4 days.
- Codeshare/regional partner flights are reported under their operating carrier and are out of
  scope.
- Automated download may be blocked by network restrictions; manual download is an accepted path.
- Crew-base choice here is a proposal; it is confirmed in Phase 2/3.
- Out of scope: actual (flown) times, delays, passenger data, aircraft type lookup per tail.
