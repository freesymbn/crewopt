# Research: Flight Data Pipeline (Phase 1)

Each decision lists what was chosen, why, and the alternatives that were rejected.

## R1. Time-zone source for airports
- **Decision**: `airportsdata` package, IATA index → `tz` (IANA name).
- **Rationale**: Offline, versioned (pinned in `uv.lock`), contains ~8k airports with IANA time zones;
  verified for DEN (America/Denver), MCO (America/New_York), HNL (Pacific/Honolulu),
  SJU (America/Puerto_Rico), STT (America/St_Thomas).
- **Alternatives**: OurAirports `airports.csv` has no time-zone column → would need
  `timezonefinder` (lat/lon → tz): an extra step and an extra dependency. OurAirports stays as a
  coordinate cross-check only. Hard-coded table: unmaintainable.

## R2. Local → UTC conversion
- **Decision**: Python `zoneinfo` with the airport's IANA zone on the flight's local date;
  vectorised per time zone (group by tz, `tz_localize` then `tz_convert("UTC")`).
- **Rationale**: Correct DST handling by construction; no third-party tz database.
- **Ambiguous/non-existent local times** (DST change night): `tz_localize(ambiguous="raise",
  nonexistent="raise")` in tests; in production, flights falling into such a gap are reported,
  never silently shifted.

## R3. Arrival date inference
- **Decision**: Arrival local date = flight date; convert to UTC; if arrival UTC ≤ departure UTC,
  add one day to the local arrival date and convert again. Then compare (arrival − departure) with
  scheduled elapsed time (FR-019).
- **Rationale**: Uses only scheduled local times (what passengers and crews see) and gives an
  independent cross-check against elapsed time.
- **Alternative**: Arrival = departure UTC + scheduled elapsed time. Simpler, but then there is
  nothing left to cross-check, and errors in either field would go unnoticed.

## R4. "hhmm" parsing
- **Decision**: Parse as integer; hours = v // 100, minutes = v % 100; 2400 → 00:00 next day;
  reject minutes ≥ 60 or hours > 24.
- **Rationale**: BTS stores times as integers ("905" = 09:05).

## R5. Raw data acquisition
- **Decision**: `fetch` command tries
  `https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{YYYY}_{M}.zip`;
  on failure it prints the URL and the expected target path (`data/raw/bts/`). The reader accepts
  the zip directly (no manual unzip).
- **Rationale**: PREZIP gives the full monthly file with tail and flight numbers. The download is
  blocked in some environments, so manual download must remain first-class (FR-002).
- **Columns read**: FlightDate, Reporting_Airline, Tail_Number, Flight_Number_Reporting_Airline,
  Origin, Dest, CRSDepTime, CRSArrTime, CRSElapsedTime, Cancelled, Diverted, Distance.

## R6. Output format
- **Decision**: Parquet (pyarrow) for flights; JSON for metadata and validation; Markdown for the
  exploration summary.
- **Rationale**: Parquet keeps types (timestamps with tz, ints) and is fast; JSON/Markdown are
  human-readable.
- **Determinism (FR-012)**: rows sorted by (dep_utc, flight_id); a **data checksum** = SHA-256 of
  a canonical CSV rendering of the sorted table is stored in metadata and used by the determinism
  test (Parquet file bytes can differ across library versions, the canonical checksum does not).

## R7. Flight identifier
- **Decision**: `{carrier}{flight_number}-{flight_date:%Y%m%d}-{origin}` (e.g. `F91234-20260913-DEN`).
- **Rationale**: Human-readable, stable, unique in BTS data except true duplicates, which FR-016 /
  duplicate detection catches.

## R8. Week and carrier defaults
- **Decision**: Configured in `config/data.yaml`; the carrier comparison (US 4) is run first on the
  downloaded month and the choice + reason recorded in metadata.
- **Rationale**: Keeps the decision evidence-based; candidates default to Frontier (F9) and
  Spirit (NK), both A320-family operators.

## R9. Crew-base proposal rule
- **Decision**: Sort airports by departures; take the smallest prefix (max 3) whose cumulative
  share ≥ 50%.
- **Rationale**: Simple, explainable, configurable; confirmed manually in Phase 2/3.
