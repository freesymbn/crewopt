# Verification: Flight Data Pipeline (Phase 1) on real data

**Date**: 2026-11-25 · **Source**: BTS On-Time Performance, September 2026
(`On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2026_9.zip`, 570,266 rows)
**Dataset**: `F9_2026-09-14` (Frontier, week 2026-09-14 … 09-20 + buffer to 09-23)

## Success criteria

| Criterion | Result | Evidence |
|---|---|---|
| SC-001 UTC times, none arrives before departing | ✅ | All 4 blocking checks pass on 5,776 flights |
| SC-002 Hand-check ≥10 flights (≥2 midnight crossings, ≥1 non-contiguous U.S.) | ✅ | Table below: 11 flights, 4 midnight crossings, 2 San Juan (SJU) |
| SC-003 Seeded defects detected | ✅ | `tests/data/test_validate.py` (defects fixture) |
| SC-004 Deterministic | ✅ | Two builds: `data_sha256` = `247c2c5e…a663d2a` both times |
| SC-005 Tail continuity ≥ 95% | ✅ | 97.8% over 5,615 consecutive-aircraft pairs |
| SC-006 Build < 2 min | ✅ | 7.4 s on the laptop (compare-carriers 10.8 s) |
| SC-007 Reproducible from the data guide | ✅ | `data/README.md` updated with exact commands |

Strongest single signal: **0 of 5,776 flights** disagree with BTS's own scheduled elapsed time
by more than 5 minutes, so the local→UTC conversion (incl. 403 midnight crossings and 239
San Juan flights) is consistent with an independent field.

## Hand-check (UTC converted back to local, compared with the raw schedule)

| Flight | Route | Raw schedule | Our UTC | Back to local | Block / elapsed | OK |
|---|---|---|---|---|---|---|
| F92802-20260922-LAS | LAS→DTW | 2151→0455 local | 09-23 04:51→09-23 08:55 UTC | 2151→0455 (09-23) | 244/244 | ✅ |
| F91670-20260915-ATL | ATL→RDU | 2255→0029 local | 09-16 02:55→09-16 04:29 UTC | 2255→0029 (09-16) | 94/94 | ✅ |
| F92508-20260923-MCO | MCO→PHL | 2136→0009 local | 09-24 01:36→09-24 04:09 UTC | 2136→0009 (09-24) | 153/153 | ✅ |
| F91725-20260923-SJU | SJU→PHL | 1727→2127 local | 09-23 21:27→09-24 01:27 UTC | 1727→2127 (09-23) | 240/240 | ✅ |
| F92249-20260921-SJU | SJU→MCO | 1842→2152 local | 09-21 22:42→09-22 01:52 UTC | 1842→2152 (09-21) | 190/190 | ✅ |
| F92836-20260918-TPA | TPA→PHL | 2155→0030 local | 09-19 01:55→09-19 04:30 UTC | 2155→0030 (09-19) | 155/155 | ✅ |
| F91816-20260918-DEN | DEN→AUS | 1616→1929 local | 09-18 22:16→09-19 00:29 UTC | 1616→1929 (09-18) | 133/133 | ✅ |
| F92276-20260923-SEA | SEA→ONT | 1053→1345 local | 09-23 17:53→09-23 20:45 UTC | 1053→1345 (09-23) | 172/172 | ✅ |
| F92045-20260923-LAS | LAS→OAK | 1015→1151 local | 09-23 17:15→09-23 18:51 UTC | 1015→1151 (09-23) | 96/96 | ✅ |
| F92505-20260923-PHL | PHL→MCO | 1745→2031 local | 09-23 21:45→09-24 00:31 UTC | 1745→2031 (09-23) | 166/166 | ✅ |
| F91544-20260914-CLE | CLE→RSW | 1729→2016 local | 09-14 21:29→09-15 00:16 UTC | 1729→2016 (09-14) | 167/167 | ✅ |
## Run summary

- Raw rows 570,266 → F9 18,106 → in window 5,831 → excluded: cancelled 35, diverted 20,
  duplicates 0, bad time 0, unknown time zone 0 → **final 5,776** (week 4,180, buffer 1,596)
- 73 airports, 161 aircraft, block time 62–323 min (median 151)

## Findings to carry into Phase 2

1. **Tail overlap warning (105 pairs, 1.9%)**: BTS records the aircraft that actually flew
   (after day-of-operation tail swaps) next to the *scheduled* times, so a swapped aircraft can
   look double-booked. Median overlap 48 min. Not a data error for crew pairing (crews follow
   the schedule), but the "same aircraft" connection feature is approximate.
2. **Crew bases**: Frontier is point-to-point, not hub-and-spoke: the top 3 airports (DEN, MCO,
   ATL) cover only 29% of departures, so the default rule (≥50%, max 3) stops at its cap. Base
   choice must be revisited in Phase 2 (more bases, or a sub-network around chosen bases).
3. **Example rotation** in the summary shows a break for the busiest aircraft; the route string
   should mark where the break is (cosmetic, Phase 2 backlog).
