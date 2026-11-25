"""Exploration summary, crew-base proposal and carrier comparison (spec US3, US4)."""

from __future__ import annotations

from datetime import date

import pandas as pd


def _week(flights: pd.DataFrame) -> pd.DataFrame:
    return flights[~flights["is_buffer"]]


def propose_bases(
    flights: pd.DataFrame, base_max: int, min_share: float
) -> list[tuple[str, float]]:
    """Smallest set of top departure airports (max base_max) covering >= min_share (research R9)."""
    dep = _week(flights)["origin"].value_counts()
    dep = dep.sort_index().sort_values(ascending=False, kind="mergesort")  # ties: by code
    total = dep.sum()
    bases, covered = [], 0
    for code, n in dep.items():
        bases.append((code, round(n / total, 3)))
        covered += n
        if covered / total >= min_share or len(bases) == base_max:
            break
    return bases


def daily_rotation(flights: pd.DataFrame, tail: str, day: date) -> pd.DataFrame:
    sel = flights[(flights["tail_number"] == tail) & (flights["flight_date"] == day)]
    return sel.sort_values("dep_utc")[
        ["flight_id", "origin", "destination", "dep_utc", "arr_utc"]
    ].reset_index(drop=True)


def summarize(flights: pd.DataFrame, base_max: int, base_min_share: float) -> dict:
    week = _week(flights)
    per_day = flights.groupby("flight_date").size()
    airports = set(flights["origin"]) | set(flights["destination"])
    dep = week["origin"].value_counts()

    busiest = week.groupby("flight_date").size().idxmax()
    on_day = week[week["flight_date"] == busiest]
    tail_counts = on_day["tail_number"].dropna().value_counts().sort_index()
    tail = tail_counts.sort_values(ascending=False, kind="mergesort").index[0]
    rot = daily_rotation(flights, tail, busiest)
    connected = bool(
        (rot["destination"].iloc[:-1].to_numpy() == rot["origin"].iloc[1:].to_numpy()).all()
    )

    return {
        "total_flights": len(flights),
        "week_flights": len(week),
        "buffer_flights": int(flights["is_buffer"].sum()),
        "airports": len(airports),
        "tails": int(flights["tail_number"].nunique()),
        "flights_per_day": {str(d): int(n) for d, n in per_day.items()},
        "block_minutes": {
            "min": int(flights["block_minutes"].min()),
            "median": float(flights["block_minutes"].median()),
            "max": int(flights["block_minutes"].max()),
        },
        "top_airports": [
            (code, int(n), round(n / len(week), 3)) for code, n in dep.head(10).items()
        ],
        "bases": propose_bases(flights, base_max, base_min_share),
        "base_rule": f"top departure airports covering >= {base_min_share:.0%}, at most {base_max}",
        "example_rotation": {
            "tail": tail,
            "date": str(busiest),
            "flights": rot["flight_id"].tolist(),
            "route": " → ".join([rot["origin"].iloc[0], *rot["destination"].tolist()]),
            "connected": connected,
        },
    }


def render_summary_md(s: dict, dataset_id: str) -> str:
    lines = [
        f"# Exploration summary: {dataset_id}",
        "",
        f"- Flights: {s['total_flights']} (week {s['week_flights']}, buffer {s['buffer_flights']})",
        f"- Airports: {s['airports']} · Aircraft (tails): {s['tails']}",
        f"- Block time (min): min {s['block_minutes']['min']}, "
        f"median {s['block_minutes']['median']:.0f}, max {s['block_minutes']['max']}",
        "",
        "## Flights per day",
        "",
        "| Date | Flights |",
        "|---|---|",
        *[f"| {d} | {n} |" for d, n in s["flights_per_day"].items()],
        "",
        "## Top departure airports (week)",
        "",
        "| Airport | Departures | Share |",
        "|---|---|---|",
        *[f"| {c} | {n} | {sh:.1%} |" for c, n, sh in s["top_airports"]],
        "",
        "## Crew-base proposal",
        "",
        f"Rule: {s['base_rule']}.",
        "",
        *[f"- **{c}** ({sh:.1%} of departures)" for c, sh in s["bases"]],
        "",
        "## Example aircraft rotation",
        "",
        f"{s['example_rotation']['tail']} on {s['example_rotation']['date']}: "
        f"{s['example_rotation']['route']} "
        f"({'connected' if s['example_rotation']['connected'] else 'NOT connected'})",
        "",
    ]
    return "\n".join(lines)


def compare_carriers(raw: pd.DataFrame, carriers: list[str] | tuple[str, ...]) -> pd.DataFrame:
    """Per-carrier size of the scheduled network in a raw month (cancelled flights excluded)."""
    sched = raw[~raw["cancelled"]]
    days = pd.to_datetime(raw["flight_date"]).nunique()
    rows = []
    for c in carriers:
        f = sched[sched["carrier"] == c]
        rows.append({
            "carrier": c,
            "flights": len(f),
            "flights_per_week": round(len(f) / days * 7, 1) if days else 0.0,
            "airports": len(set(f["origin"]) | set(f["destination"])),
            "tails": int(f["tail_number"].nunique()),
            "tail_share": round(f["tail_number"].notna().mean(), 3) if len(f) else 0.0,
        })  # fmt: skip
    return pd.DataFrame(rows)


def render_comparison_md(table: pd.DataFrame) -> str:
    header = "| Carrier | Flights | Flights/week | Airports | Tails | Tail share |"
    lines = ["# Carrier comparison", "", header, "|---|---|---|---|---|---|"]
    for r in table.itertuples():
        lines.append(
            f"| {r.carrier} | {r.flights} | {r.flights_per_week} | {r.airports} | {r.tails} "
            f"| {r.tail_share:.1%} |"
        )
    return "\n".join(lines) + "\n"
