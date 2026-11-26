"""Gaussian-process surrogate models of PPA + Bayesian optimisation (numpy only).

Why: a full flow run costs minutes to hours, so we cannot sweep every knob
combination on a real design.  We fit one GP per metric (runtime, power, area)
on the runs done so far, then choose the next batch of configurations by
Expected Improvement of the composite cost, estimated by Monte-Carlo sampling
from the per-metric posteriors.

* kernel: squared-exponential with automatic relevance determination (one
  length-scale per knob -> tells us which knobs matter)
* hyper-parameters: maximise the log marginal likelihood (random search + local refinement)
* targets: log-transformed and standardised
* batch selection: "kriging believer" (pretend the chosen point returned its
  predicted mean, refit, pick the next) so a batch can run in parallel on the cluster
* model quality: leave-one-out cross-validation (MAPE, R^2) is reported every round
"""
from __future__ import annotations

import numpy as np

from objective import METRICS


class GP:
    def __init__(self, ls=None, sf=1.0, sn=0.05):
        self.ls, self.sf, self.sn = ls, sf, sn

    def _k(self, A, B):
        d = (A[:, None, :] - B[None, :, :]) / self.ls
        return self.sf ** 2 * np.exp(-0.5 * (d ** 2).sum(-1))

    def fit(self, X, y, optimise=True, rng=None):
        self.X = np.asarray(X, float)
        self.mu, self.sd = y.mean(), y.std() + 1e-9
        self.y = (y - self.mu) / self.sd
        if self.ls is None:
            self.ls = np.ones(self.X.shape[1])
        if optimise and len(y) >= 3:
            self._optimise(rng or np.random.default_rng(0))
        self._factor()
        return self

    def _factor(self):
        K = self._k(self.X, self.X) + (self.sn ** 2 + 1e-8) * np.eye(len(self.X))
        self.L = np.linalg.cholesky(K)
        self.alpha = np.linalg.solve(self.L.T, np.linalg.solve(self.L, self.y))

    def lml(self) -> float:
        try:
            self._factor()
        except np.linalg.LinAlgError:
            return -np.inf
        return float(-0.5 * self.y @ self.alpha - np.log(np.diag(self.L)).sum()
                     - 0.5 * len(self.y) * np.log(2 * np.pi))

    def _optimise(self, rng, n_random=300, n_local=200):
        d = self.X.shape[1]
        best = (self.lml(), self.ls.copy(), self.sf, self.sn)

        def trial(ls, sf, sn):
            nonlocal best
            self.ls, self.sf, self.sn = ls, sf, sn
            v = self.lml()
            if v > best[0]:
                best = (v, ls.copy(), sf, sn)

        for _ in range(n_random):
            trial(np.exp(rng.uniform(np.log(0.2), np.log(20), d)),
                  np.exp(rng.uniform(np.log(0.3), np.log(3))), np.exp(rng.uniform(np.log(1e-3), np.log(0.5))))
        for _ in range(n_local):
            _, ls, sf, sn = best
            trial(ls * np.exp(rng.normal(0, 0.2, d)), sf * np.exp(rng.normal(0, 0.1)),
                  float(np.clip(sn * np.exp(rng.normal(0, 0.2)), 1e-4, 1)))
        _, self.ls, self.sf, self.sn = best

    def predict(self, Xs):
        Xs = np.asarray(Xs, float)
        Ks = self._k(Xs, self.X)
        m = Ks @ self.alpha
        v = np.linalg.solve(self.L, Ks.T)
        var = np.clip(self.sf ** 2 - (v ** 2).sum(0), 1e-12, None)
        return m * self.sd + self.mu, np.sqrt(var) * self.sd


class PPASurrogate:
    """One GP per metric on log(metric)."""

    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)
        self.models: dict[str, GP] = {}

    def fit(self, X, Y: dict[str, np.ndarray]):
        self.X = np.asarray(X, float)
        self.Y = {k: np.asarray(v, float) for k, v in Y.items()}
        self.models = {k: GP().fit(self.X, np.log(self.Y[k]), rng=self.rng) for k in METRICS}
        return self

    def predict(self, Xs) -> dict[str, tuple[np.ndarray, np.ndarray]]:
        """mean / std in log space per metric."""
        return {k: g.predict(Xs) for k, g in self.models.items()}

    def relevance(self, names) -> dict[str, dict[str, float]]:
        """1/length-scale per knob, normalised: which knobs drive which metric."""
        out = {}
        for k, g in self.models.items():
            r = 1 / g.ls
            out[k] = {n: round(float(v), 3) for n, v in zip(names, r / r.sum())}
        return out

    def loo(self) -> dict[str, dict[str, float]]:
        """Leave-one-out CV with fixed hyper-parameters (model accuracy on unseen configs)."""
        res = {}
        n = len(self.X)
        if n < 4:
            return res
        for k, g in self.models.items():
            y = np.log(self.Y[k])
            pred = []
            for i in range(n):
                msk = np.arange(n) != i
                gi = GP(g.ls, g.sf, g.sn).fit(self.X[msk], y[msk], optimise=False)
                pred.append(gi.predict(self.X[i:i + 1])[0][0])
            p, t = np.exp(pred), self.Y[k]
            ss = ((t - p) ** 2).sum()
            st = ((t - t.mean()) ** 2).sum() + 1e-12
            res[k] = {"mape_pct": round(float(100 * np.mean(np.abs(p - t) / t)), 2),
                      "r2": round(float(1 - ss / st), 3)}
        return res


def expected_improvement(sur: PPASurrogate, Xc, ref: dict, w: dict, best: float,
                         n_mc: int = 512, rng=None) -> tuple[np.ndarray, np.ndarray]:
    """MC estimate of E[max(best - cost(x), 0)] and the predicted mean cost."""
    rng = rng or np.random.default_rng(1)
    pred = sur.predict(Xc)
    c = np.zeros((n_mc, len(Xc)))
    for k in METRICS:
        m, s = pred[k]
        c += w[k] * np.exp(m + s * rng.standard_normal((n_mc, len(Xc)))) / ref[k]
    return np.maximum(best - c, 0).mean(0), c.mean(0)


def propose_batch(X, Y, candidates, ref, w, k=4, seed=0) -> list[dict]:
    """Kriging-believer batch Bayesian optimisation over a discrete candidate set."""
    X, cand = [list(x) for x in X], [list(c) for c in candidates]
    Y = {m: list(v) for m, v in Y.items()}
    chosen = []
    for _ in range(min(k, len(cand))):
        sur = PPASurrogate(seed).fit(X, {m: np.array(v) for m, v in Y.items()})
        cost_obs = sum(w[m] * np.array(Y[m]) / ref[m] for m in METRICS)
        ei, mc = expected_improvement(sur, np.array(cand), ref, w, cost_obs.min())
        i = int(np.argmax(ei))
        chosen.append({"x": [int(v) for v in cand[i]], "ei": float(ei[i]), "pred_cost": float(mc[i])})
        mu = sur.predict(np.array([cand[i]]))
        X.append(cand[i])                               # believe the mean, refit
        for m in METRICS:
            Y[m].append(float(np.exp(mu[m][0][0])))
        cand.pop(i)
    return chosen
