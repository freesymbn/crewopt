# Data

Nothing under `data/raw/` or `data/processed/` is committed. Recreate it as follows.

## 1. Flights — BTS On-Time Performance
- Source: https://www.transtats.bts.gov → Aviation → *Airline On-Time Performance Data*
  ("Reporting Carrier On-Time Performance").
- Use the **Download** page: tail number and flight number are only available there.
- One month per download. Save the zip/csv into `data/raw/bts/`.
- Columns we need (phase 1 spec will finalize): FlightDate, Reporting_Airline, Tail_Number,
  Flight_Number_Reporting_Airline, Origin, Dest, CRSDepTime, CRSArrTime, CRSElapsedTime,
  Cancelled, Diverted, Distance.

## 2. Airports — OurAirports
- Source: https://ourairports.com/data/ → `airports.csv` (already in `data/raw/airports.csv`).
- Used for coordinates. Time zones: see phase 1 spec (OurAirports has no tz column).

## 3. Processed outputs
Created by code in `crewopt/data/`, e.g. `data/processed/flights_<carrier>_<week>.parquet`.
