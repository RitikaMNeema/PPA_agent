"""Fast unit tests (no EDA tools needed): guardrails, objective, surrogate, DSE encoding."""
import itertools
import json

import numpy as np
import pytest

from candidates import FORBIDDEN, PatchError, apply_patch
from executor import FlowJob
from objective import DEFAULT_WEIGHTS, cost, metrics_of, pareto_front
from surrogate import GP, PPASurrogate, propose_batch

RTL = {"core.v": "always @(posedge clk) a <= b;\nalways @(posedge clk) c <= d;\n"}


# ---------------------------------------------------------------- guardrails
def test_patch_applies_exact_unique_match():
    out = apply_patch(RTL, {"edits": [{"file": "core.v", "search": "a <= b;", "replace": "a <= b & en;"}]})
    assert "a <= b & en;" in out["core.v"] and RTL["core.v"] != out["core.v"]


def test_patch_rejects_ambiguous_search():
    with pytest.raises(PatchError, match="matches 2 times"):
        apply_patch(RTL, {"edits": [{"file": "core.v", "search": "always @(posedge clk)", "replace": "x"}]})


def test_patch_rejects_missing_search():
    with pytest.raises(PatchError, match="matches 0 times"):
        apply_patch(RTL, {"edits": [{"file": "core.v", "search": "nonexistent", "replace": "x"}]})


def test_patch_rejects_unknown_file():
    with pytest.raises(PatchError, match="unknown file"):
        apply_patch(RTL, {"edits": [{"file": "other.v", "search": "a", "replace": "b"}]})


@pytest.mark.parametrize("name", sorted(FORBIDDEN))
def test_forbidden_params_rejected(name):
    with pytest.raises(PatchError, match="forbidden"):
        apply_patch(RTL, {"params": [{"name": name, "value": 0}]})


# ---------------------------------------------------------------- objective
PPA = {"workload_cycles": 600000, "fmax_mhz": 100.0, "power_mw_at_target": 10.0, "area_um2": 1e5}


def test_reference_cost_is_one():
    m = metrics_of(PPA)
    assert cost(m, m) == pytest.approx(sum(DEFAULT_WEIGHTS.values()))


def test_metrics_need_power():
    assert metrics_of({k: v for k, v in PPA.items() if k != "power_mw_at_target"}) is None


def test_pareto_front():
    pts = [{"runtime": 1, "power": 2, "area": 3}, {"runtime": 2, "power": 1, "area": 3},
           {"runtime": 2, "power": 2, "area": 3}]                      # last one is dominated
    assert pareto_front(pts) == [0, 1]


# ---------------------------------------------------------------- surrogate / BO
def _synthetic(X):
    X = np.asarray(X)
    return {"runtime": 7000 * (1 + .3 * X[:, 3] - .2 * X[:, 1]),
            "power": 12 * (1 + .15 * X[:, 1] - .05 * X[:, 6]),
            "area": 1e5 * (1 + .2 * X[:, 1] - .04 * X[:, 6])}


def test_gp_interpolates():
    X = np.array([[0.], [1.], [2.], [3.]])
    g = GP().fit(X, np.sin(X[:, 0]))
    m, s = g.predict(X)
    assert np.allclose(m, np.sin(X[:, 0]), atol=0.1) and (s >= 0).all()


def test_surrogate_learns_and_ranks_knobs():
    P = np.array(list(itertools.product([0, 1], repeat=7)))
    idx = np.random.default_rng(0).choice(len(P), 14, replace=False)
    sur = PPASurrogate().fit(P[idx], _synthetic(P[idx]))
    assert all(v["r2"] > 0.9 for v in sur.loo().values())
    rel = sur.relevance([f"k{i}" for i in range(7)])
    assert max(rel["runtime"], key=rel["runtime"].get) in ("k1", "k3")


def test_bo_batch_is_distinct_and_untested():
    P = [list(x) for x in itertools.product([0, 1], repeat=7)]
    train = P[::9]
    Y = {k: list(v) for k, v in _synthetic(train).items()}
    ref = {k: v[0] for k, v in Y.items()}
    cand = [x for x in P if x not in train]
    batch = propose_batch(train, Y, cand, ref, DEFAULT_WEIGHTS, k=4)
    xs = [tuple(b["x"]) for b in batch]
    assert len(set(xs)) == 4 and not set(xs) & {tuple(t) for t in train}
    json.dumps(batch)                                                 # serialisable for the logs


# ---------------------------------------------------------------- DSE / executor
def test_dse_encode_decode_roundtrip():
    from dse import SPACE, all_points, base_cfg, decode, encode, tag_of
    base = base_cfg()
    for x in all_points()[:: 17]:
        assert encode(decode(x, base)) == x
    assert len(all_points()) == 2 ** len(SPACE)
    assert tag_of([0, 1, 0]) == "dse_010"


def test_flow_job_is_json_serialisable():
    d = FlowJob("t", "cfg.json", 1000, meta={"x": [1, 0]}).to_dict()
    assert json.loads(json.dumps(d))["meta"]["x"] == [1, 0]
