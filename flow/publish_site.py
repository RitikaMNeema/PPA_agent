"""Build a static, read-only copy of the dashboards into docs/ for GitHub Pages.

    python flow/publish_site.py

docs/
  index.html                 landing page -> the three dashboards
  dashboard.html             runs, PPA, stage status, log links
  bottlenecks.html           bottlenecks + RTL suggestions (buttons need the local server)
  explore.html               Bayesian-optimisation DSE + agent sessions
  <run>/...                  the linked reports/logs (files <= 1 MB; larger ones are not linked)
"""
from __future__ import annotations

import re
import shutil

import dashboard
from env import ROOT, RUNS

DOCS = ROOT / "docs"
MAX_BYTES = 1_000_000

INDEX = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PPA_agent</title>
<style>
:root{color-scheme:light;--bg:#f4f3f0;--surface:#fcfcfb;--border:#e2e1dc;--text:#0b0b0b;--muted:#52514e;--accent:#2a78d6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#121211;--surface:#1a1a19;--border:#2e2e2b;--text:#f0efec;--muted:#c3c2b7;--accent:#3987e5}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#121211;--surface:#1a1a19;--border:#2e2e2b;--text:#f0efec;--muted:#c3c2b7;--accent:#3987e5}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:860px;margin:0 auto;padding:40px 16px}
h1{font-size:26px;margin:0 0 6px}
p{color:var(--muted);margin:0 0 20px}
a.card{display:block;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 18px;margin-bottom:12px;color:inherit;text-decoration:none}
a.card:hover{border-color:var(--accent)}
a.card b{color:var(--accent)}
.note{font-size:13px}
</style></head><body><div class="wrap">
<h1>PPA_agent</h1>
<p>AI agent and Bayesian optimisation improving the power, performance and area of a RISC-V core (PicoRV32,
sky130) on an open-source ASIC flow, with flow runs distributed on Spark. These are static snapshots of the
project's dashboards. Source and write-up: <a href="https://github.com/RitikaMNeema/PPA_agent">GitHub repository</a>.</p>
<a class="card" href="dashboard.html"><b>Flow dashboard →</b><br>Every flow run: area, timing, power, stage status, and links to logs and reports.</a>
<a class="card" href="explore.html"><b>Exploration &amp; agent →</b><br>Bayesian-optimisation sweep run on Spark (surrogate accuracy, knob relevance, Pareto front) and the closed-loop agent's step-by-step decisions.</a>
<a class="card" href="bottlenecks.html"><b>Bottlenecks &amp; RTL suggestions →</b><br>Top power, timing and congestion bottlenecks traced to RTL lines, with suggested RTL patches as diffs.</a>
<p class="note">Snapshot generated __DATE__. The Generate and Run buttons only work with the local server (<code>python flow/serve.py</code>).</p>
</div></body></html>
"""


# local absolute paths in tool logs -> placeholders (plain, escaped and forward-slash forms)
SEP = r"(?:\\\\|\\|/)"
SCRUB = [(re.compile(r"[A-Za-z]:" + SEP + r"Ritika_Gemma4" + SEP + r"(?:vlsi_agent|PPA_agent)"), "<repo>"),
         (re.compile(r"[A-Za-z]:" + SEP + r"Users" + SEP + r"[^\\/\"'\s]+"), "<home>")]


def scrub():
    for p in DOCS.rglob("*"):
        if not p.is_file():
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        t = s
        for rx, rep in SCRUB:
            t = rx.sub(rep, t)
        if t != s:
            p.write_text(t, encoding="utf-8")


def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    runs = dashboard.collect()
    for m in runs:                                   # linked artefacts, size-capped
        for _, rel, _ in dashboard.FILES:
            src = RUNS / m["tag"] / rel
            if src.exists() and src.stat().st_size <= MAX_BYTES:
                dst = DOCS / m["tag"] / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, dst)
    orig = dashboard.run_files                       # only link what was published
    dashboard.run_files = lambda rd: [f for f in orig(rd) if (DOCS / f["href"]).exists()]
    try:
        dashboard.build(DOCS / "dashboard.html")
    finally:
        dashboard.run_files = orig
    for f in ("dashboard.html", "bottlenecks.html", "explore.html"):
        p = DOCS / f
        p.write_text(re.sub(r'<meta http-equiv="refresh"[^>]*>\n?', "", p.read_text(encoding="utf-8")),
                     encoding="utf-8")
    scrub()
    from datetime import date
    (DOCS / "index.html").write_text(INDEX.replace("__DATE__", date.today().isoformat()), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("")              # serve .md/.json files as-is
    n = sum(1 for p in DOCS.rglob("*") if p.is_file())
    mb = sum(p.stat().st_size for p in DOCS.rglob("*") if p.is_file()) / 1e6
    print(f"docs/: {n} files, {mb:.1f} MB")


if __name__ == "__main__":
    main()
