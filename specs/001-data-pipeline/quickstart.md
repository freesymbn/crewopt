# Quickstart: Flight Data Pipeline (Phase 1)

## 1. Get the raw data
```bash
uv run python -m crewopt.data fetch --year 2026 --month 8
```
If it fails, download the printed URL in a browser and save the zip to `data/raw/bts/`.

## 2. Choose the carrier
```bash
uv run python -m crewopt.data compare-carriers --raw data/raw/bts/<file>.zip
```
Pick the carrier and week; write them into `config/data.yaml` with a one-line reason.

## 3. Build the dataset
```bash
uv run python -m crewopt.data build
```
Expect exit code 0 and "valid: true".

## 4. Verify (acceptance)
- Open `flights_<id>.validation.json`: all blocking checks `pass` (SC-001).
- Open `flights_<id>.summary.md`: tail continuity ≥ 95% or explained (SC-005).
- Hand-check ≥10 flights incl. 2 midnight crossings and 1 HNL/SJU flight against a public
  schedule, converting UTC back to local (SC-002).
- Run `build` twice: `data_sha256` in both metadata files is equal (SC-004).
- `uv run pytest` is green, including the seeded-defect test (SC-003).
