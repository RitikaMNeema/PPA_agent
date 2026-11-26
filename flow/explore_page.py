"""HTML template for runs/explore.html: design-space exploration (Bayesian optimisation
on the compute backend) and agent sessions.  Built by dashboard.build_explore()."""

ETEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PPA Exploration</title>
<style>/*__STYLE__*/
.chart{width:100%;height:auto;display:block}
.bar{height:8px;border-radius:4px;background:var(--series-1)}
td .bar{min-width:2px}
.k2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.pill{font-size:11px;padding:0 6px;border-radius:99px;background:var(--chip);color:var(--text-secondary)}
</style></head><body>
<div class="wrap">
<header><h1>Exploration &amp; agent</h1><span class="sub" id="sub"></span>
 <a class="toggle" style="text-decoration:none" href="dashboard.html">← Dashboard</a></header>
<div id="dse"></div>
<div id="agents"></div>
</div>
<div class="tip" id="tip"></div>
<script>
const D = /*__DATA__*/;
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmt = (v, d=1) => v == null ? "–" : Number(v).toLocaleString(undefined, {maximumFractionDigits:d, minimumFractionDigits:d});
const pct = (a, b) => `${a/b-1 >= 0 ? "+" : ""}${(100*(a/b-1)).toFixed(1)}%`;
const tip = $("#tip");
function showTip(e, html){ tip.innerHTML = html; tip.style.display = "block";
  const x = Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8); tip.style.left = x + "px"; tip.style.top = (e.clientY + 14) + "px"; }
function hideTip(){ tip.style.display = "none"; }
$("#sub").textContent = `generated ${D.generated}`;

function scale(d0, d1, r0, r1){ const k = (r1 - r0) / ((d1 - d0) || 1); return v => r0 + (v - d0) * k; }
function ticks(a, b, n=5){ const s = (b - a) / n, p = Math.pow(10, Math.floor(Math.log10(s))), m = [1,2,2.5,5,10].find(m => m*p >= s) * p;
  const out = []; for (let v = Math.ceil(a/m)*m; v <= b + 1e-9; v += m) out.push(+v.toFixed(10)); return out; }
function axes(W, H, P, xs, ys, xd, yd, xl, yl){
  let g = "";
  const dec = tk => tk.length > 1 ? Math.max(0, Math.ceil(-Math.log10(tk[1] - tk[0]) + 1e-9)) : 0;
  const yt = ticks(...yd), xt = ticks(...xd), yp = dec(yt), xp = dec(xt);
  for (const t of yt) g += `<line x1="${P.l}" x2="${W-P.r}" y1="${ys(t)}" y2="${ys(t)}" stroke="var(--grid)"/>`+
      `<text x="${P.l-6}" y="${ys(t)+4}" text-anchor="end">${fmt(t, yp)}</text>`;
  for (const t of xt) g += `<text x="${xs(t)}" y="${H-P.b+16}" text-anchor="middle">${fmt(t, xp)}</text>`;
  g += `<line x1="${P.l}" x2="${W-P.r}" y1="${H-P.b}" y2="${H-P.b}" stroke="var(--border)"/>`;
  g += `<text x="${(P.l+W-P.r)/2}" y="${H-4}" text-anchor="middle">${xl}</text>`;
  g += `<text transform="translate(12 ${(P.t+H-P.b)/2}) rotate(-90)" text-anchor="middle">${yl}</text>`;
  return g;
}
const pad = (a, b, f=.08) => { const d = (b - a) || Math.abs(a) * .1 || 1; return [a - d*f, b + d*f]; };

function renderDSE(S){
  if (!S){ $("#dse").innerHTML = `<div class="card empty">No design-space exploration yet — <code>python flow/dse.py --executor spark</code></div>`; return; }
  const ref = S.reference, best = S.best, T = S.table;
  const loo = S.loo_final || {};
  const tiles = [
    ["Configurations evaluated", `${S.evaluated}<small> / ${S.space_size}</small>`, `${S.ok} passed verification`],
    ["Best PPA cost", `${fmt(best.cost, 3)}<small> vs 1.000</small>`, `<code>${best.tag}</code>`],
    ["Parallel speed-up", `×${fmt(S.cpu_seconds / Math.max(1, S.wall_seconds), 1)}`, `${S.executor} · ${S.workers} workers · ${fmt(S.wall_seconds/60,1)} min wall`],
    ["Surrogate error (LOO)", Object.values(loo).length ? `${fmt(Math.max(...Object.values(loo).map(v => v.mape_pct)), 1)}<small>% max MAPE</small>` : "–",
       Object.entries(loo).map(([k, v]) => `${k} R² ${v.r2}`).join(" · ")],
  ];
  let h = `<div class="tiles" style="margin-bottom:16px">` + tiles.map(([k, v, d]) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div>`).join("") + `</div>`;
  h += `<div class="k2"><div class="card"><h2>Runtime vs power — each point is one full flow run</h2><div id="scat"></div>
        <div class="legend"><span><span class="sw" style="background:var(--series-1)"></span>initial (random)</span>
        <span><span class="sw" style="background:var(--series-2)"></span>chosen by Bayesian optimisation</span>
        <span>◆ reference · ring = Pareto-optimal</span></div></div>
        <div class="card"><h2>Best cost found vs number of flow runs</h2><div id="conv"></div>
        <div class="legend"><span><span class="sw" style="background:var(--series-1)"></span>best-so-far cost (lower is better)</span></div></div></div>`;
  h += `<div class="card"><h2>Best configuration vs reference</h2><div class="scroll"><table><tr><th>knob</th><th>reference</th><th>best</th></tr>` +
       Object.entries(best.knobs).map(([k, v]) => { const r = (T.find(t => t.tag === ref.tag) || {knobs:{}}).knobs[k];
         return `<tr><td>${k}</td><td>${r}</td><td>${v}${r !== v ? ' <span class="pill">changed</span>' : ""}</td></tr>`; }).join("") +
       `</table></div><p class="muted">runtime ${pct(best.runtime, ref.runtime)} · power ${pct(best.power, ref.power)} · area ${pct(best.area, ref.area)} · power window ${fmt(S.pwr_cycles,0)} cycles · weights ${esc(JSON.stringify(S.weights))}</p></div>`;
  const rel = S.relevance_final, mets = Object.keys(rel);
  h += `<div class="card"><h2>Which knobs drive which metric (GP relevance = 1 / length-scale)</h2><div class="scroll"><table><tr><th>knob</th>${mets.map(m => `<th>${m}</th>`).join("")}</tr>` +
       Object.keys(rel[mets[0]]).map(k => `<tr><td>${k}</td>${mets.map(m => `<td><div style="display:flex;gap:8px;align-items:center"><div class="bar" style="width:${Math.round(rel[m][k]*120)}px"></div>${fmt(rel[m][k],2)}</div></td>`).join("")}</tr>`).join("") +
       `</table></div></div>`;
  h += `<div class="card"><h2>All runs</h2><div class="scroll"><table><tr><th>tag</th><th>round</th><th>source</th><th class="num">runtime µs</th><th class="num">power mW</th><th class="num">area µm²</th><th class="num">cost</th><th class="num">flow s</th><th>host</th></tr>` +
       T.map(t => `<tr><td><code>${t.tag}</code>${S.pareto.includes(t.tag) ? ' <span class="pill">Pareto</span>' : ""}</td><td>${t.round}</td><td>${t.source}</td><td class="num">${fmt(t.metrics.runtime,0)}</td><td class="num">${fmt(t.metrics.power,3)}</td><td class="num">${fmt(t.metrics.area,0)}</td><td class="num">${fmt(t.cost,4)}</td><td class="num">${fmt(t.seconds,0)}</td><td>${esc(t.host)}</td></tr>`).join("") +
       `</table></div></div>`;
  $("#dse").innerHTML = h;

  // scatter
  { const W = 560, H = 340, P = {l:56, r:16, t:12, b:40};
    const xd = pad(Math.min(...T.map(t => t.metrics.runtime)), Math.max(...T.map(t => t.metrics.runtime)));
    const yd = pad(Math.min(...T.map(t => t.metrics.power)), Math.max(...T.map(t => t.metrics.power)));
    const xs = scale(...xd, P.l, W-P.r), ys = scale(...yd, H-P.b, P.t);
    let g = axes(W, H, P, xs, ys, xd, yd, "workload runtime (µs, lower = faster)", "power (mW)");
    T.forEach((t, i) => {
      const x = xs(t.metrics.runtime), y = ys(t.metrics.power), c = t.source === "bo" ? "var(--series-2)" : "var(--series-1)";
      const pr = S.pareto.includes(t.tag);
      if (pr) g += `<circle cx="${x}" cy="${y}" r="9" fill="none" stroke="var(--text-secondary)" stroke-width="1.5"/>`;
      g += t.tag === ref.tag ? `<path d="M${x} ${y-7}L${x+7} ${y}L${x} ${y+7}L${x-7} ${y}Z" fill="${c}" stroke="var(--surface-1)" stroke-width="2"/>`
                             : `<circle cx="${x}" cy="${y}" r="5" fill="${c}" stroke="var(--surface-1)" stroke-width="2"/>`;
      g += `<circle cx="${x}" cy="${y}" r="12" fill="transparent" data-i="${i}" class="hit"/>`;
    });
    $("#scat").innerHTML = `<svg class="chart" viewBox="0 0 ${W} ${H}">${g}</svg>`;
    $("#scat").querySelectorAll(".hit").forEach(el => {
      const t = T[+el.dataset.i];
      el.addEventListener("mousemove", e => showTip(e, `<b>${t.tag}</b> (${t.source}, round ${t.round})<br>runtime ${fmt(t.metrics.runtime,0)} µs · power ${fmt(t.metrics.power,3)} mW<br>area ${fmt(t.metrics.area,0)} µm² · cost ${fmt(t.cost,4)}<br><span class="muted">${Object.entries(t.knobs).map(([k,v]) => `${k}=${v}`).join(", ")}</span>`));
      el.addEventListener("mouseleave", hideTip);
    });
  }
  // convergence (order of evaluation = round, then table order by round)
  { const seq = [...T].sort((a, b) => a.round - b.round); let bsf = Infinity;
    const pts = seq.map((t, i) => { bsf = Math.min(bsf, t.cost); return {i: i + 1, c: bsf, t, round: t.round}; });
    const W = 560, H = 340, P = {l:56, r:16, t:12, b:40};
    const xd = [1, Math.max(2, pts.length)], yd = pad(Math.min(...pts.map(p => p.c)), Math.max(...pts.map(p => p.c)), .2);
    const xs = scale(...xd, P.l, W-P.r), ys = scale(...yd, H-P.b, P.t);
    let g = axes(W, H, P, xs, ys, xd, yd, "flow runs completed", "best cost so far");
    const rounds = [...new Set(pts.map(p => p.round))];
    rounds.slice(1).forEach(r => { const p = pts.find(q => q.round === r); const x = xs(p.i - .5);
      g += `<line x1="${x}" x2="${x}" y1="${P.t}" y2="${H-P.b}" stroke="var(--border)" stroke-dasharray="3 3"/><text x="${x+4}" y="${P.t+10}">BO round ${r}</text>`; });
    g += `<path d="${pts.map((p, k) => `${k ? "H" + xs(p.i) + "V" : "M" + xs(p.i) + " "}${ys(p.c)}`).join("")}" fill="none" stroke="var(--series-1)" stroke-width="2"/>`;
    pts.forEach((p, k) => g += `<circle cx="${xs(p.i)}" cy="${ys(p.c)}" r="10" fill="transparent" class="hit" data-k="${k}"/>`);
    $("#conv").innerHTML = `<svg class="chart" viewBox="0 0 ${W} ${H}">${g}</svg>`;
    $("#conv").querySelectorAll(".hit").forEach(el => { const p = pts[+el.dataset.k];
      el.addEventListener("mousemove", e => showTip(e, `after ${p.i} runs: best cost <b>${fmt(p.c,4)}</b><br>this run ${p.t.tag} (${p.t.source}) cost ${fmt(p.t.cost,4)}`));
      el.addEventListener("mouseleave", hideTip); });
  }
}

function renderAgents(A){
  if (!A.length){ $("#agents").innerHTML = `<div class="card empty">No agent sessions yet — <code>python flow/agent.py</code></div>`; return; }
  $("#agents").innerHTML = A.map(T => {
    const r = T.reference || {};
    let h = `<div class="card"><h2>Agent session <code>${esc(T.session)}</code> <span class="badge ${T.status === "done" ? "ok" : "run"}">${T.status}</span></h2>
      <p class="muted">base ${esc(T.base_run)} · proposer <b>${T.proposer}</b> · executor ${T.executor} ×${T.parallel} · window ${fmt(T.pwr_cycles,0)} cycles${T.llm ? ` · LLM ${T.llm.calls} calls, $${T.llm.spent_usd} of $${T.llm.budget_usd}` : ""}${T.wall_seconds ? ` · ${fmt(T.wall_seconds/60,1)} min` : ""}</p>`;
    if (T.accepted) h += `<div class="scroll"><table><tr><th>step</th><th>accepted change</th><th class="num">cost</th><th class="num">runtime</th><th class="num">power</th><th class="num">area</th></tr>` +
      T.accepted.map(a => `<tr><td>${a.step}</td><td>${esc(a.change)}</td><td class="num">${fmt(a.cost,4)}</td><td class="num">${pct(a.metrics.runtime, r.runtime)}</td><td class="num">${pct(a.metrics.power, r.power)}</td><td class="num">${pct(a.metrics.area, r.area)}</td></tr>`).join("") + `</table></div>`;
    for (const s of T.steps) {
      h += `<h2 style="margin-top:16px">Step ${s.step} <span class="muted">from ${esc(s.from)} (cost ${fmt(s.from_cost,4)})</span></h2>`;
      if (s.evaluated.length) h += `<div class="scroll"><table><tr><th>candidate</th><th>category</th><th>verdict</th><th class="num">cost</th><th class="num">Δruntime</th><th class="num">Δpower</th><th class="num">Δarea</th><th class="num">flow s</th></tr>` +
        s.evaluated.map(e => { const d = e.delta_pct || {}; const f = k => d[k] == null ? "–" : `${d[k] >= 0 ? "+" : ""}${d[k].toFixed(1)}%`;
          return `<tr><td>${esc(e.title)}</td><td>${e.category}</td><td>${e.verdict ? `<span class="badge bad">${esc(e.verdict)}</span>` : `<span class="badge ok">verified</span>`}</td><td class="num">${fmt(e.cost,4)}</td><td class="num">${f("runtime")}</td><td class="num">${f("power")}</td><td class="num">${f("area")}</td><td class="num">${fmt(e.seconds,0)}</td></tr>`; }).join("") + `</table></div>`;
      if (s.rejected.length) h += `<p class="muted">Rejected before running: ${s.rejected.map(x => `${esc(x.title)} (${esc(x.reason)})`).join("; ")}</p>`;
      h += `<p><b>Decision:</b> ${esc(s.decision || "running…")}</p>`;
    }
    return h + `</div>`;
  }).join("");
}
renderDSE(D.dse); renderAgents(D.agents);
</script></body></html>"""
