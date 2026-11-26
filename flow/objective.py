"""PPA objective shared by the DSE optimiser and the agent loop.

Lower is better.  Each metric is normalised by a reference run measured with the
*same* power window, so the weighted sum is unit-free:

    runtime   = workload cycles / Fmax        (performance: captures both CPI and frequency)
    power     = average power at the target clock
    area      = standard-cell area

    cost = w_t * runtime/runtime_ref + w_p * power/power_ref + w_a * area/area_ref
"""
from __future__ import annotations

DEFAULT_WEIGHTS = {"runtime": 0.4, "power": 0.4, "area": 0.2}
METRICS = ("runtime", "power", "area")


def metrics_of(ppa: dict) -> dict | None:
    if not ppa or "power_mw_at_target" not in ppa:
        return None
    return {"runtime": ppa["workload_cycles"] / ppa["fmax_mhz"],      # us
            "power": ppa["power_mw_at_target"],
            "area": ppa["area_um2"]}


def cost(m: dict, ref: dict, w: dict = DEFAULT_WEIGHTS) -> float:
    return sum(w[k] * m[k] / ref[k] for k in METRICS)


def pareto_front(points: list[dict], keys=METRICS) -> list[int]:
    """Indices of non-dominated points (minimise every key)."""
    idx = []
    for i, p in enumerate(points):
        dominated = any(all(q[k] <= p[k] for k in keys) and any(q[k] < p[k] for k in keys)
                        for j, q in enumerate(points) if j != i)
        if not dominated:
            idx.append(i)
    return idx
