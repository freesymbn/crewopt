# crewopt

Airline **crew pairing** optimization with **hybrid column generation and machine learning**.

> Work in progress. A learning project on how airline crew planning is optimized and how an
> optimization model is taken from prototype to a production-ready service.

## The problem
An airline needs a cockpit crew on every flight. Crews live at a **base**, start their work there
and must return there after a few days. Such a multi-day sequence of flights from base back to
base is a **pairing**. Crew pairing finds a set of legal pairings that covers every flight at
minimum cost (duty days, hotel nights, deadheads, waiting time, time away from base).

The number of possible pairings explodes combinatorially, so they cannot all be enumerated.

## Approach
- **Column generation**: solve the LP relaxation over a small pool of pairings, use the dual
  values to search the flight network for new pairings with negative reduced cost
  (resource-constrained shortest path), repeat, then solve the integer problem.
- **Machine learning**: a classifier scores flight-to-flight connections by how likely they are to
  appear in good solutions. It prunes the pricing network and warm-starts the master problem.
- **Safety net**: a final pricing pass on the full network, so ML errors cannot degrade
  solution quality.
- Legal rules (connection times, duty and rest limits) are hard constraints kept in
  `config/rules.yaml`, separate from the algorithms.

## Data
- Flights: U.S. Bureau of Transportation Statistics, On-Time Performance (scheduled times,
  tail numbers)
- Airports: OurAirports
- See [`data/README.md`](data/README.md) to recreate the datasets.

## Quick start
```bash
uv sync
uv run pytest
```

## Roadmap
| # | Phase |
|---|---|
| 0 | Project setup |
| 1 | Data: download, explore, clean |
| 2 | Domain model + rule engine |
| 3 | Flight connection network |
| 4 | Baseline: enumeration + MIP on a small instance |
| 5 | Classic column generation |
| 6 | ML connection scorer |
| 7 | Hybrid CG + ML and benchmark |
| 8 | Production: job API, queue, monitoring, security, environments |

## References
- Zeren, Özcan, Deveci (2024). *An adaptive greedy heuristic for large scale airline crew pairing
  problems.* Journal of Air Transport Management.
- Kasirzadeh, Saddoune, Soumis (2017). *Airline crew scheduling: models, algorithms, and data sets.*
  EURO Journal on Transportation and Logistics.
- Parmentier, Meunier (2019). *Aircraft routing and crew pairing: updated algorithms at Air France.*
- Yaakoubi, Soumis, Lacoste-Julien (2020). *Machine learning in airline crew pairing to construct
  initial clusters for dynamic constraint aggregation.* EURO Journal on Transportation and Logistics.

## Tech
Python · Pyomo · HiGHS · pandas · scikit-learn · LightGBM · pytest · uv
