# Contract: Output files

For dataset id `<carrier>_<YYYY-MM-DD>` (week Monday), in `data/processed/`:

| File | Content | Consumer |
|---|---|---|
| `flights_<id>.parquet` | Flight table, schema in [data-model.md](../data-model.md#flight-one-row-of-flights_carrier_weekparquet) | Phases 2–7 |
| `flights_<id>.meta.json` | Dataset metadata (provenance, counts, checksums) | Reproducibility, later phases |
| `flights_<id>.validation.json` | ValidationReport | Gate before later phases |
| `flights_<id>.summary.md` | Exploration summary + crew-base proposal | Human |

Stability promise: column names and types of the Parquet file do not change without a new
feature spec; later phases may rely on them.
