# Data

Nothing under `data/raw/` or `data/processed/` is committed. Recreate it as follows.

## Quick commands

```bash
# 1. get the month file (if blocked, download the printed URL in a browser into data/raw/bts/)
uv run python -m crewopt.data fetch --year 2026 --month 9
# 2. compare candidate carriers, then set carrier/week in config/data.yaml
uv run python -m crewopt.data compare-carriers \
  --raw data/raw/bts/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2026_9.zip
# 3. build the weekly dataset (exit 0 = valid, 2 = blocking check failed)
uv run python -m crewopt.data build
```

Current dataset: Frontier (F9), week of 2026-09-14, from the September 2026 file
(direct link: https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2026_9.zip).

## 1. Flights — BTS On-Time Performance
- Source: https://www.transtats.bts.gov → Aviation → *Airline On-Time Performance Data*
  ("Reporting Carrier On-Time Performance").
- Use the **Download** page: tail number and flight number are only available there.
- One month per download. Save the zip/csv into `data/raw/bts/`.
- Columns used: FlightDate, Reporting_Airline, Tail_Number,
  Flight_Number_Reporting_Airline, Origin, Dest, CRSDepTime, CRSArrTime, CRSElapsedTime,
  Cancelled, Diverted, Distance.

## 2. Airports — OurAirports
- Source: https://ourairports.com/data/ → `airports.csv` (already in `data/raw/airports.csv`).
- Optional, coordinates only. Time zones come from the `airportsdata` package (installed by `uv sync`).

## 3. Processed outputs
Created by `build` in `data/processed/`: `flights_<id>.parquet`, `.meta.json`, `.validation.json`,
`.summary.md` (see `specs/001-data-pipeline/contracts/outputs.md`).
