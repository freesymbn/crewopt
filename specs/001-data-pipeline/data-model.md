# Data Model: Flight Data Pipeline (Phase 1)

## Flight (one row of `flights_<carrier>_<week>.parquet`)

| Field | Type | Rules / meaning |
|---|---|---|
| flight_id | string | `{carrier}{flight_number}-{YYYYMMDD}-{origin}`; unique (FR-016) |
| carrier | string | IATA code of the reporting carrier (e.g. `F9`) |
| flight_number | int | Carrier's flight number |
| tail_number | string \| null | Aircraft registration; null allowed, flagged (FR-020) |
| flight_date | date | Local scheduled departure date (as in BTS) |
| origin, destination | string | IATA airport codes; origin ≠ destination (FR-015) |
| dep_local, arr_local | timestamp (tz-aware, airport zone) | Scheduled local times |
| dep_utc, arr_utc | timestamp (UTC) | arr_utc > dep_utc (FR-013) |
| block_minutes | int | (arr_utc − dep_utc) in minutes; within configured range (FR-014) |
| crs_elapsed_minutes | int | BTS scheduled elapsed time; cross-check (FR-019) |
| distance_miles | int | From BTS |
| is_buffer | bool | True for flights after the selected week (FR-009) |

Sort order: `dep_utc`, then `flight_id`.

## Airport

| Field | Type | Rules |
|---|---|---|
| code | string | IATA |
| name | string | |
| lat, lon | float | |
| tz | string | IANA zone; required for every airport used (FR-003) |

## Dataset metadata (`*.meta.json`)

| Field | Meaning |
|---|---|
| dataset_id | `<carrier>_<week_monday>` |
| source_file, source_sha256 | Raw month file and checksum |
| carrier, carrier_selection_reason | FR-011, US 4 |
| week_start, week_end, buffer_days | Selection window |
| config_sha256 | Hash of the config used |
| created_utc, package_version, airportsdata_version | Run provenance |
| counts | raw_rows, carrier_rows, in_window, excluded_by_reason{cancelled, diverted, unknown_tz, duplicate, bad_time}, final, buffer |
| data_sha256 | Canonical checksum of the flight table (R6) |
| valid | Copied from the validation report |

## ValidationReport (`*.validation.json`)

| Field | Meaning |
|---|---|
| valid | True only if all blocking checks pass |
| checks[] | `{id, name, severity: blocking\|warning, status: pass\|fail\|warn, count, examples[≤10], detail}` |

Check ids: `arrival_after_departure` (FR-013), `block_time_range` (FR-014),
`airports_known_and_distinct` (FR-015), `unique_ids` (FR-016), `tail_continuity` (FR-017),
`tail_overlap` (FR-018), `elapsed_time_consistency` (FR-019), `missing_tail` (FR-020).

## State / flow

```
raw month zip ─► read (needed columns) ─► filter carrier + window ─► drop cancelled/diverted
   ─► parse times ─► attach airport tz (unknown → excluded) ─► local→UTC + arrival inference
   ─► ids + dedupe + buffer flag ─► sort ─► validate ─► write parquet + meta + validation
   ─► exploration summary
```
