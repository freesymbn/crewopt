# Contract: Command-line interface

All commands: `uv run python -m crewopt.data <command> [options]`. Exit code 0 = success,
1 = error (message on stderr), 2 = dataset produced but **not valid** (blocking check failed).

## fetch
`fetch --year YYYY --month M`
- Downloads the BTS PREZIP month file into `data/raw/bts/`.
- If the download fails: exit 1 and print the exact URL and target path for manual download.

## compare-carriers
`compare-carriers --raw <path-to-zip-or-csv> [--carriers F9,NK]`
- Prints and writes `data/processed/carrier_comparison_<YYYY>_<MM>.md`: per carrier and per
  week — flights, airports, tails, share of flights with tail number.

## build
`build [--config config/data.yaml]`
- Runs the full pipeline for the configured carrier/week.
- Writes the four outputs listed in [outputs.md](outputs.md).
- Prints a run summary: counts per exclusion reason, validity, output paths.
