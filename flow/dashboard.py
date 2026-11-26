"""Live PPA dashboard: runs/dashboard.html, rebuilt from runs/*/metrics.json.

    python flow/dashboard.py            # build once
    python flow/dashboard.py --watch    # rebuild every few seconds (page auto-refreshes)

run_flow.py also rebuilds it after every stage, so a running iteration shows
its live stage progress.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from env import BUILD, RUNS

STAGES = [("lint", "Lint"), ("rtl_sim", "RTL sim"), ("synth", "Synthesis"),
          ("sta", "STA"), ("gls", "Gate-level sim"), ("power", "Power")]


def collect() -> list[dict]:
    runs = []
    for mf in RUNS.glob("*/metrics.json"):
        if mf.parent.name.startswith(("_", "dse_")):      # DSE sweeps have their own page
            continue
        try:
            m = json.loads(mf.read_text())
        except Exception:
            continue
        started = (mf.parent / "inputs").stat().st_mtime
        m["_started"] = started
        m["_updated"] = mf.stat().st_mtime
        # live stage status
        st, seen_fail = [], m["status"].startswith("fail")
        running_marked = False
        for key, label in STAGES:
            if key in m["stages"]:
                s = m["stages"][key]
                ok = s.get("ok", s.get("pass", True))
                if key == "gls" and s.get("fail_reason") is None:
                    ok = True
                st.append({"key": key, "label": label, "state": "done" if ok else "failed",
                           "secs": s.get("seconds")})
            elif m["status"] == "running" and not running_marked:
                st.append({"key": key, "label": label, "state": "running",
                           "secs": round(time.time() - m["_updated"])})
                running_marked = True
            else:
                st.append({"key": key, "label": label, "state": "skipped" if seen_fail or m["status"] == "ok" else "pending"})
        m["_stages"] = st
        runs.append(m)
    runs.sort(key=lambda r: r["_started"])
    return runs


def slim(m: dict) -> dict:
    s = m["stages"]
    out = {"tag": m["tag"], "status": m["status"], "started": m["_started"], "updated": m["_updated"],
           "stages": m["_stages"], "params": m.get("params", {}), "synth_opts": m.get("synth_opts", {}),
           "constraints": m.get("constraints", {}), "ppa": m.get("ppa", {}), "sha": m.get("inputs_sha")}
    if "synth" in s and s["synth"].get("ok"):
        sy = s["synth"]
        out["synth"] = {k: sy[k] for k in ("area_um2", "seq_area_um2", "comb_area_um2", "num_cells", "num_ff",
                                           "cell_families_top")}
    if "sta" in s:
        t = s["sta"]
        out["sta"] = {k: t[k] for k in ("wns_ns", "tns_ns", "n_failing", "n_endpoints", "fmax_mhz",
                                        "clock_period_ns", "worst_endpoint_groups")}
        cp = t["critical_paths"][0]
        out["sta"]["cp"] = {k: cp[k] for k in ("startpoint", "endpoint", "slack_ns", "logic_depth")}
        out["sta"]["cp"]["path"] = cp["path"]
    if "rtl_sim" in s:
        out["rtl_sim"] = s["rtl_sim"]
    if "power" in s:
        out["power"] = s["power"]
    out["files"] = run_files(RUNS / m["tag"])
    return out


# (group, relative path, label) — only files that exist are linked
FILES = [
    ("Synthesis", "synth/yosys.log", "Yosys log"),
    ("Synthesis", "synth/stat.txt", "cell / area report"),
    ("Synthesis", "synth/synth.ys", "Yosys script"),
    ("Synthesis", "synth/abc.script", "ABC script"),
    ("Synthesis", "synth/netlist.v", "gate netlist (.v)"),
    ("Verification", "logs/lint.log", "lint (Verilator)"),
    ("Verification", "logs/rtl_sim.log", "RTL sim (firmware console)"),
    ("Verification", "logs/gls_sim.log", "gate-level sim"),
    ("Power", "power/cells_sim.v", "generated cell models"),
    ("Inputs", "inputs/config.json", "config (knobs)"),
    ("Inputs", "inputs/picorv32.sdc", "SDC constraints"),
    ("Inputs", "inputs/top.v", "top wrapper"),
    ("Reports", "report.md", "PPA report (md)"),
    ("Reports", "metrics.json", "metrics.json"),
    ("Reports", "bottlenecks.json", "bottlenecks.json"),
    ("Reports", "advice.json", "AI / rule advice (json)"),
]


def run_files(rd: Path) -> list[dict]:
    out = []
    for grp, rel, label in FILES:
        f = rd / rel
        if f.exists():
            kb = f.stat().st_size / 1024
            out.append({"group": grp, "href": f"{rd.name}/{rel}", "label": label,
                        "size": f"{kb / 1024:.1f} MB" if kb > 1024 else f"{kb:.0f} KB"})
    return out


def build(path: Path | None = None, refresh: int = 5) -> Path:
    path = path or RUNS / "dashboard.html"
    runs = [slim(m) for m in collect()]
    data = json.dumps({"generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "runs": runs})
    live = any(r["status"] == "running" for r in runs)
    html = TEMPLATE.replace("/*__DATA__*/", data).replace("__REFRESH__", str(refresh if live else 30))
    tmp = path.with_suffix(".tmp")
    tmp.write_text(html, encoding="utf-8")
    tmp.replace(path)
    try:
        build_bottlenecks(path.parent / "bottlenecks.html", runs)
    except Exception as e:  # never break the main dashboard
        print(f"[bottlenecks page] {e}")
    try:
        build_explore(path.parent / "explore.html")
    except Exception as e:
        print(f"[explore page] {e}")
    return path


def build_explore(path: Path) -> Path:
    """Third page: design-space exploration + agent sessions."""
    import importlib
    import explore_page
    sf = RUNS / "dse" / "summary.json"
    agents = []
    for tf in sorted((RUNS / "agent").glob("*/trajectory.json")) if (RUNS / "agent").exists() else []:
        try:
            agents.append(json.loads(tf.read_text()))
        except Exception:
            pass
    agents.sort(key=lambda t: t.get("started", ""), reverse=True)
    data = json.dumps({"generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "dse": json.loads(sf.read_text()) if sf.exists() else None, "agents": agents})
    style = TEMPLATE.split("<style>", 1)[1].split("</style>", 1)[0]
    html = importlib.reload(explore_page).ETEMPLATE.replace("/*__STYLE__*/", style) \
        .replace("/*__DATA__*/", data.replace("</", "<\\/"))
    tmp = path.with_suffix(".tmp")
    tmp.write_text(html, encoding="utf-8")
    tmp.replace(path)
    return path


def build_bottlenecks(path: Path, runs: list[dict]) -> Path:
    """Second page: per-category bottlenecks + AI (or rule-based) RTL feedback."""
    from advisor import rule_based
    from bottlenecks import extract
    pages = []
    for r in runs:
        rd = RUNS / r["tag"]
        if r["status"] != "ok":
            continue
        af = rd / "advice.json"
        if not af.exists():            # first time: deterministic draft, no LLM call
            b = extract(rd)
            (rd / "bottlenecks.json").write_text(json.dumps(b, indent=2))
            af.write_text(json.dumps({"tag": r["tag"], "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                      "bottlenecks": b, "rules": rule_based(b), "llm": None,
                                      "llm_error": "not requested yet"}, indent=2))
        pg = json.loads(af.read_text())
        from candidates import preview
        for src in ("rules", "llm"):
            for c in ("power", "timing", "congestion"):
                for s in ((pg.get(src) or {}).get(c) or {}).get("suggestions", []):
                    s["_preview"] = preview(r["tag"], s)     # suggested new RTL (diff) or why not
        pages.append(pg)
    from candidates import CAND_DIR
    cands = []
    for mf in sorted(CAND_DIR.glob("*/meta.json")) if CAND_DIR.exists() else []:
        if not mf.parent.name.startswith("_"):
            cm = json.loads(mf.read_text())
            rm = RUNS / cm["name"] / "metrics.json"
            cm["run_status"] = json.loads(rm.read_text())["status"] if rm.exists() else None
            cands.append(cm)
    pv = BUILD / "patch_verify.json"
    data = json.dumps({"generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pages": pages,
                       "candidates": cands, "patch_verify": json.loads(pv.read_text()) if pv.exists() else {}})
    import importlib
    import bottlenecks_page                      # reloaded so template edits show up in --watch mode
    BTEMPLATE = importlib.reload(bottlenecks_page).BTEMPLATE
    style = TEMPLATE.split("<style>", 1)[1].split("</style>", 1)[0]
    html = BTEMPLATE.replace("/*__STYLE__*/", style).replace("/*__DATA__*/", data.replace("</", "<\\/"))
    tmp = path.with_suffix(".tmp")
    tmp.write_text(html, encoding="utf-8")
    tmp.replace(path)
    return path


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="__REFRESH__">
<title>PPA Agent Dashboard</title>
<style>
:root{color-scheme:light;
 --bg:#f4f3f0;--surface-1:#fcfcfb;--border:#e2e1dc;--grid:#ebeae6;
 --text-primary:#0b0b0b;--text-secondary:#52514e;--text-muted:#77766f;
 --series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;--series-4:#eda100;
 --good:#0ca30c;--good-text:#006300;--warning:#fab219;--critical:#d03b3b;--critical-text:#b02a2a;
 --running:#2a78d6;--chip:#f0efec}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;
 --bg:#121211;--surface-1:#1a1a19;--border:#2e2e2b;--grid:#262624;
 --text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#8f8e86;
 --series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;--series-4:#c98500;
 --good:#0ca30c;--good-text:#4cc24c;--critical:#d03b3b;--critical-text:#ec7b7b;--running:#3987e5;--chip:#262624}}
:root[data-theme="dark"]{color-scheme:dark;
 --bg:#121211;--surface-1:#1a1a19;--border:#2e2e2b;--grid:#262624;
 --text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#8f8e86;
 --series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;--series-4:#c98500;
 --good:#0ca30c;--good-text:#4cc24c;--critical:#d03b3b;--critical-text:#ec7b7b;--running:#3987e5;--chip:#262624}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text-primary);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1200px;margin:0 auto;padding:20px 16px 48px}
header{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 16px;margin-bottom:16px}
h1{font-size:20px;margin:0;font-weight:650}
.sub{color:var(--text-secondary)}
.muted{color:var(--text-muted);font-size:12px}
.card{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:16px}
.card h2{font-size:14px;margin:0 0 12px;font-weight:600}
.grid{display:grid;gap:16px}
.g2{grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.tile{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:14px}
.tile .k{color:var(--text-secondary);font-size:12px}
.tile .v{font-size:26px;font-weight:650;margin-top:2px;font-variant-numeric:tabular-nums}
.tile .v small{font-size:13px;font-weight:500;color:var(--text-secondary)}
.tile .d{font-size:12px;margin-top:4px;color:var(--text-secondary)}
.badge{display:inline-flex;align-items:center;gap:4px;font-size:12px;padding:1px 8px;border-radius:99px;background:var(--chip);color:var(--text-secondary)}
.badge.ok{color:var(--good-text)} .badge.bad{color:var(--critical-text)} .badge.run{color:var(--running)}
.pipe{display:flex;flex-wrap:wrap;gap:8px}
.stage{flex:1 1 130px;border:1px solid var(--border);border-radius:8px;padding:10px;min-width:120px}
.stage .n{font-weight:600;font-size:13px}
.stage .s{font-size:12px;color:var(--text-secondary);margin-top:2px;display:flex;gap:6px;align-items:center}
.dot{width:8px;height:8px;border-radius:50%;background:var(--text-muted);flex:none}
.stage.done .dot{background:var(--good)} .stage.failed .dot{background:var(--critical)}
.stage.running{border-color:var(--running)} .stage.running .dot{background:var(--running);animation:pulse 1.2s infinite}
@keyframes pulse{50%{opacity:.25}}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--grid);white-space:nowrap}
th{font-weight:600;color:var(--text-secondary);font-size:12px}
td.num,th.num{text-align:right}
.scroll{overflow-x:auto}
code,pre{font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace}
pre{margin:0;white-space:pre;overflow:auto;max-height:380px;color:var(--text-secondary)}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;font-size:12px;color:var(--text-secondary)}
.sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.tip{position:fixed;pointer-events:none;background:var(--surface-1);border:1px solid var(--border);border-radius:8px;
 padding:8px 10px;font-size:12px;box-shadow:0 4px 16px rgba(0,0,0,.15);display:none;z-index:9;max-width:320px}
.tip b{font-weight:600}
svg text{fill:var(--text-secondary);font-size:11px}
.toggle{margin-left:auto;background:var(--chip);border:1px solid var(--border);color:var(--text-secondary);border-radius:6px;padding:3px 10px;cursor:pointer;font:inherit;font-size:12px}
.empty{color:var(--text-muted);font-size:13px;padding:8px 0}
.card.empty{padding:14px 16px}
table.kv td{white-space:normal}table.kv td.num{word-break:break-word}
</style></head>
<body><div class="wrap" id="app"></div><div class="tip" id="tip"></div>
<script>
const D = /*__DATA__*/;
try{const t=localStorage.getItem('ppa-theme'); if(t) document.documentElement.dataset.theme=t;}catch(e){}
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt=(v,d=1)=>v==null?'–':Number(v).toLocaleString(undefined,{maximumFractionDigits:d,minimumFractionDigits:d});
const runs=D.runs, done=runs.filter(r=>r.status==='ok'), base=done[0], last=done[done.length-1];
const cur=runs.filter(r=>r.status==='running').pop()||runs[runs.length-1];
const tip=$('#tip');
function showTip(e,html){tip.innerHTML=html;tip.style.display='block';const x=Math.min(e.clientX+14,innerWidth-tip.offsetWidth-8);tip.style.left=x+'px';tip.style.top=(e.clientY+14)+'px'}
function hideTip(){tip.style.display='none'}
function delta(v,b,lowerBetter,d=1,unit=''){if(v==null||b==null||v===b)return '';const p=100*(v-b)/Math.abs(b);
 const good=lowerBetter?p<0:p>0;return `<span style="color:var(${good?'--good-text':'--critical-text'})">${p>0?'▲':'▼'} ${fmt(Math.abs(p),1)}% vs baseline</span>`}
function age(ts){const s=Math.round(Date.now()/1000-ts);return s<90?s+' s ago':s<5400?Math.round(s/60)+' min ago':Math.round(s/3600)+' h ago'}

function header(){const live=runs.some(r=>r.status==='running');
 return `<header><h1>PPA Agent · PicoRV32</h1><span class="sub">sky130_fd_sc_hd · tt 25°C 1.80 V · Yosys/ABC + custom STA &amp; activity power</span>
 <span class="badge ${live?'run':''}">${live?'● live — refreshing every few seconds':'idle'}</span>
 <a class="toggle" style="text-decoration:none" href="bottlenecks.html" target="_blank">Bottlenecks &amp; AI feedback ↗</a>
 <a class="toggle" style="text-decoration:none;margin-left:0" href="explore.html" target="_blank">Exploration &amp; agent ↗</a>
 <button class="toggle" style="margin-left:0" onclick="flip()">theme</button>
 <div class="muted" style="flex-basis:100%">generated ${esc(D.generated)} · ${runs.length} run(s)</div></header>`}
window.flip=()=>{const r=document.documentElement;const dark=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
 r.dataset.theme=dark?'light':'dark';try{localStorage.setItem('ppa-theme',r.dataset.theme)}catch(e){}}

function pipeline(r){if(!r)return '';
 const lab={done:'done',failed:'failed',running:'running…',pending:'pending',skipped:'skipped'};
 return `<div class="card"><h2>Current run · <code>${esc(r.tag)}</code> <span class="badge ${r.status==='ok'?'ok':r.status==='running'?'run':'bad'}">${esc(r.status)}</span>
 <span class="muted" style="font-weight:400"> · started ${age(r.started)} · inputs ${esc(r.sha||'')}</span></h2>
 <div class="pipe">${r.stages.map(s=>`<div class="stage ${s.state}"><div class="n">${s.label}</div>
 <div class="s"><span class="dot"></span>${lab[s.state]}${s.secs!=null?` · ${s.state==='running'?'≥':''}${fmt(s.secs,0)} s`:''}</div></div>`).join('')}</div></div>`}

function tiles(r){if(!r)return '<div class="card empty">No completed run yet — tiles appear when the first iteration finishes.</div>';
 const p=r.ppa,b=base.ppa, met=p.timing_met;
 const T=(k,v,d)=>`<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d||'&nbsp;'}</div></div>`;
 return `<div class="tiles" style="margin-bottom:16px">
 ${T('Power @ '+fmt(p.target_mhz,0)+' MHz', p.power_mw_at_target!=null?`${fmt(p.power_mw_at_target,2)} <small>mW</small>`:'<small>pending</small>', r===base?'baseline':delta(p.power_mw_at_target,b.power_mw_at_target,true))}
 ${T('Fmax', `${fmt(p.fmax_mhz,1)} <small>MHz</small>`, `<span class="badge ${met?'ok':'bad'}">${met?'✓ timing met':'✗ WNS '+fmt(p.wns_ns,2)+' ns'}</span> ${r===base?'':delta(p.fmax_mhz,b.fmax_mhz,false)}`)}
 ${T('Cell area', `${fmt(p.area_um2/1000,1)}k <small>µm²</small>`, r===base?`${fmt(p.num_cells,0)} cells · ${fmt(p.num_ff,0)} flops`:delta(p.area_um2,b.area_um2,true))}
 ${T('Energy / workload', p.workload_energy_uj!=null?`${fmt(p.workload_energy_uj,1)} <small>µJ</small>`:'<small>pending</small>', r===base?(p.energy_per_cycle_pj!=null?fmt(p.energy_per_cycle_pj,1)+' pJ/cycle':''):delta(p.workload_energy_uj,b.workload_energy_uj,true))}
 ${T('Workload runtime', `${fmt(p.workload_runtime_us_at_fmax/1000,2)} <small>ms @ Fmax</small>`, `CPI ${fmt(p.cpi,2)} · ${fmt(p.workload_cycles,0)} cycles`)}
 </div>`}

// single-series trend line (small multiple); one point per completed iteration
function trend(title,key,unit,d,lowerBetter){
 const pts=done.map((r,i)=>({i,tag:r.tag,v:r.ppa[key]})).filter(p=>p.v!=null);
 if(!pts.length)return `<div class="card"><h2>${title}</h2><div class="empty">waiting for data</div></div>`;
 const W=360,H=150,L=44,R=12,Tp=12,B=26, vs=pts.map(p=>p.v); let lo=Math.min(...vs),hi=Math.max(...vs);
 const pad=(hi-lo)*0.15||Math.abs(hi)*0.05||1; lo-=pad; hi+=pad;
 const x=i=>pts.length===1?L+(W-L-R)/2:L+i*(W-L-R)/(pts.length-1), y=v=>Tp+(hi-v)*(H-Tp-B)/(hi-lo);
 const ticks=[lo+ (hi-lo)*0.1, (lo+hi)/2, hi-(hi-lo)*0.1];
 const id='t_'+key;
 const path=pts.map((p,k)=>(k?'L':'M')+x(k).toFixed(1)+','+y(p.v).toFixed(1)).join('');
 const lastp=pts[pts.length-1];
 return `<div class="card"><h2>${title} <span class="muted" style="font-weight:400">(${unit}${lowerBetter?', lower is better':', higher is better'})</span></h2>
 <svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="${title} per iteration" id="${id}">
 ${ticks.map(t=>`<line x1="${L}" x2="${W-R}" y1="${y(t)}" y2="${y(t)}" stroke="var(--grid)"/><text x="${L-6}" y="${y(t)+4}" text-anchor="end">${fmt(t,d)}</text>`).join('')}
 <path d="${path}" fill="none" stroke="var(--series-1)" stroke-width="2" stroke-linejoin="round"/>
 ${pts.map((p,k)=>`<circle cx="${x(k)}" cy="${y(p.v)}" r="4.5" fill="var(--series-1)" stroke="var(--surface-1)" stroke-width="2"/>
   <text x="${x(k)}" y="${H-8}" text-anchor="middle">${k===0?'base':'#'+k}</text>`).join('')}
 <text x="${x(pts.length-1)+(pts.length>1?4:0)}" y="${y(lastp.v)-10}" text-anchor="${pts.length>1?'end':'middle'}" style="fill:var(--text-primary);font-weight:600">${fmt(lastp.v,d)}</text>
 ${pts.map((p,k)=>`<rect x="${x(k)-18}" y="0" width="36" height="${H}" fill="transparent" data-tip="<b>${esc(p.tag)}</b><br>${title}: ${fmt(p.v,d)} ${unit}"/>`).join('')}
 </svg></div>`}

const PCOMP=[['clock_mw','Clock','--series-1'],['sequential_mw','Sequential','--series-2'],['combinational_mw','Combinational','--series-3'],['leakage_mw','Leakage','--series-4']];
function powerBreak(r){const pw=r&&r.power; if(!pw)return `<div class="card"><h2>Power breakdown</h2><div class="empty">pending — gate-level simulation of the workload is still running</div></div>`;
 const tot=pw.total_mw, W=600, H=34; let x0=0;
 const segs=PCOMP.map(([k,l,c])=>{const w=Math.max(0,pw[k]/tot*W);const s={k,l,c,x:x0,w,v:pw[k]};x0+=w;return s});
 return `<div class="card"><h2>Power breakdown · ${fmt(tot,3)} mW @ ${fmt(pw.freq_mhz,0)} MHz <span class="muted" style="font-weight:400">· ${fmt(pw.window_cycles,0)}-cycle window</span></h2>
 <svg viewBox="0 0 ${W} ${H}" width="100%" preserveAspectRatio="none" style="height:34px" role="img" aria-label="power breakdown">
 ${segs.filter(s=>s.w>0).map((s,i,a)=>`<rect x="${s.x+(i?1:0)}" y="0" width="${Math.max(0,s.w-(i?1:0)-(i<a.length-1?1:0))}" height="${H}" rx="4" fill="var(${s.c})"
  data-tip="<b>${s.l}</b><br>${fmt(s.v,4)} mW · ${fmt(100*s.v/tot,1)}%"/>`).join('')}</svg>
 <div class="legend">${segs.map(s=>`<span><span class="sw" style="background:var(${s.c})"></span>${s.l} <b style="color:var(--text-primary)">${fmt(100*s.v/tot,1)}%</b> · ${s.k==='leakage_mw'?fmt(pw.leakage_uw,3)+' µW':fmt(s.v,3)+' mW'}</span>`).join('')}</div>
 <div class="muted" style="margin-top:8px">internal ${fmt(pw.internal_mw,3)} mW · switching ${fmt(pw.switching_mw,3)} mW · avg net toggle rate ${fmt(pw.avg_net_toggle_rate,4)}/cycle · clock pin cap ${fmt(pw.clock_pin_cap_pf,2)} pF</div></div>`}

function regBars(r){const pw=r&&r.power; if(!pw)return `<div class="card"><h2>Top registers by power</h2><div class="empty">pending</div></div>`;
 const rows=pw.top_registers_by_power.slice(0,10), mx=Math.max(...rows.map(x=>x.power_mw));
 return `<div class="card"><h2>Top registers by power <span class="muted" style="font-weight:400">(clock + output switching + internal)</span></h2>
 ${rows.map(x=>`<div style="display:grid;grid-template-columns:minmax(120px,1.3fr) 2fr 64px;gap:8px;align-items:center;margin:5px 0"
   data-tip="<b>${esc(x.register)}</b><br>${fmt(x.power_mw,3)} mW · ${x.n_ff} flops<br>toggle rate ${fmt(x.toggle_rate,4)}/cycle">
  <code style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(x.register)}">${esc(x.register.replace(/^core\.(genblk\d\.)*/,''))}</code>
  <div style="height:12px;background:var(--grid);border-radius:4px"><div style="height:12px;width:${100*x.power_mw/mx}%;background:var(--series-1);border-radius:4px"></div></div>
  <span style="text-align:right;font-variant-numeric:tabular-nums">${fmt(x.power_mw,3)}</span></div>`).join('')}</div>`}

function timing(r){const t=r&&r.sta; if(!t)return '';
 const g=t.worst_endpoint_groups.slice(0,8);
 const cp=t.cp, steps=cp.path;
 return `<div class="grid g2"><div class="card"><h2>Worst endpoint groups <span class="muted" style="font-weight:400">· period ${t.clock_period_ns} ns · ${t.n_failing}/${t.n_endpoints} failing</span></h2>
 <div class="scroll"><table><tr><th>register / port</th><th class="num">WNS ns</th><th class="num">failing</th></tr>
 ${g.map(x=>`<tr><td><code>${esc(x.endpoint_group.replace(/^core\.(genblk\d\.)*/,''))}</code></td><td class="num" style="color:var(${x.wns_ns<0?'--critical-text':'--good-text'})">${fmt(x.wns_ns,3)}</td><td class="num">${x.n_failing}/${x.n_endpoints}</td></tr>`).join('')}
 </table></div></div>
 <div class="card"><h2>Critical path · slack <span style="color:var(${cp.slack_ns<0?'--critical-text':'--good-text'})">${fmt(cp.slack_ns,3)} ns</span> · depth ${cp.logic_depth}</h2>
 <div class="muted" style="margin-bottom:6px"><code>${esc(cp.startpoint)}</code> → <code>${esc(cp.endpoint)}</code></div>
 <pre>${steps.map(s=>`${fmt(s.arrival,3).padStart(7)}  +${fmt(s.incr,3)}  ${s.cell.padEnd(10)} ${esc(s.net.length>44?s.net.slice(0,44)+'…':s.net)}`).join('\n')}</pre></div></div>`}

// ---- overall PPA summary for one run (works while power is still running) ----
function summary(r){if(!r||!r.synth)return '';
 const sy=r.synth,t=r.sta||{},pw=r.power,c=r.constraints||{},rs=r.rtl_sim||{},p=r.ppa||{};
 const per=c.period||t.clock_period_ns, pend='<span class="muted">pending</span>';
 const bad=v=>v!=null&&v<0?'--critical-text':'--good-text';
 const sec=(title,rows)=>`<div><div class="muted" style="text-transform:uppercase;letter-spacing:.04em;margin:0 0 4px">${title}</div>
  <table class="kv">${rows.map(([k,v])=>`<tr><td style="color:var(--text-secondary)">${k}</td><td class="num">${v}</td></tr>`).join('')}</table></div>`;
 return `<div class="card"><h2>Design PPA summary · <code>${esc(r.tag)}</code></h2>
 <div class="grid" style="gap:20px;grid-template-columns:repeat(auto-fit,minmax(340px,1fr))">
 ${sec('Design &amp; library',[
   ['Top / core','<code>picorv32_top</code> (RV32IMC)'],
   ['Library','sky130_fd_sc_hd'],['Corner','tt · 25°C · 1.80 V'],
   ['Synthesis',`Yosys + ABC (${esc((r.synth_opts||{}).abc_script||'speed')})`]])}
 ${sec('Clocks &amp; constraints',[
   ['Clocks',`1 · <code>${esc(c.clock_port||'clk')}</code>`],
   ['Target frequency',`<b>${fmt(1000/per,1)} MHz</b> (${fmt(per,2)} ns)`],
   ['Uncertainty / transition',`${fmt(c.uncertainty,2)} / ${fmt(c.clk_slew,2)} ns`],
   ['Input / output delay',`${fmt(c.io_delay,2)} ns`],
   ['Output load',`${fmt((c.po_load||0)*1000,1)} fF`],
   ['False paths',(c.false_from||[]).map(x=>'<code>'+esc(x)+'</code>').join(', ')||'–']])}
 ${sec('Area',[
   ['Total cell area',`<b>${fmt(sy.area_um2,0)} µm²</b>`],
   ['Sequential',`${fmt(sy.seq_area_um2,0)} µm² (${fmt(100*sy.seq_area_um2/sy.area_um2,0)}%)`],
   ['Combinational',`${fmt(sy.comb_area_um2,0)} µm²`],
   ['Cell count',`<b>${fmt(sy.num_cells,0)}</b>`],['Flip-flops',fmt(sy.num_ff,0)],
   ['Combinational cells',fmt(sy.num_cells-sy.num_ff,0)]])}
 ${sec('Timing (setup)',[
   ['WNS',t.wns_ns!=null?`<b style="color:var(${bad(t.wns_ns)})">${fmt(t.wns_ns,3)} ns</b>`:pend],
   ['TNS',t.tns_ns!=null?`<b style="color:var(${bad(t.tns_ns)})">${fmt(t.tns_ns,3)} ns</b>`:pend],
   ['Failing endpoints',t.n_endpoints?`${fmt(t.n_failing,0)} / ${fmt(t.n_endpoints,0)}`:pend],
   ['Fmax',t.fmax_mhz?`<b>${fmt(t.fmax_mhz,1)} MHz</b>`:pend],
   ['Timing met',t.wns_ns==null?pend:t.wns_ns>=0?'<span class="badge ok">✓ yes</span>':'<span class="badge bad">✗ no</span>'],
   ['Logic depth (crit.)',t.cp?fmt(t.cp.logic_depth,0):pend]])}
 ${sec('Power @ target',[
   ['Total',pw?`<b>${fmt(pw.total_mw,3)} mW</b>`:pend],
   ['Clock',pw?`${fmt(pw.clock_mw,3)} mW`:pend],
   ['Sequential / comb.',pw?`${fmt(pw.sequential_mw,3)} / ${fmt(pw.combinational_mw,3)} mW`:pend],
   ['Internal / switching',pw?`${fmt(pw.internal_mw,3)} / ${fmt(pw.switching_mw,3)} mW`:pend],
   ['Leakage',pw?`<b>${fmt(pw.leakage_uw,3)} µW</b>`:pend],
   ['Energy / cycle',pw?`${fmt(pw.energy_per_cycle_pj,1)} pJ`:pend]])}
 ${sec('Performance &amp; verification',[
   ['Workload','riscv-tests + sieve + mul/div + IRQ'],
   ['Cycles / CPI',rs.cycles?`${fmt(rs.cycles,0)} / ${fmt(rs.cycles/rs.instr_fetches,2)}`:pend],
   ['Runtime @ Fmax',t.fmax_mhz&&rs.cycles?`${fmt(rs.cycles/t.fmax_mhz/1000,2)} ms`:pend],
   ['Energy / workload',p.workload_energy_uj!=null?`${fmt(p.workload_energy_uj,2)} µJ`:pend],
   ['RTL sim',rs.pass?'<span class="badge ok">✓ PASS</span>':pend],
   ['Gate-level sim',r.stages.find(s=>s.key==='gls').state==='done'?'<span class="badge ok">✓ PASS</span>':r.stages.find(s=>s.key==='gls').state]])}
 </div></div>`}

function logs(r){if(!r||!r.files||!r.files.length)return '';
 const groups=[...new Set(r.files.map(f=>f.group))];
 return `<div class="card"><h2>Logs &amp; reports · <code>${esc(r.tag)}</code></h2>
 <div class="grid g3" style="gap:12px 20px">${groups.map(g=>`<div><div class="muted" style="text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px">${g}</div>
 ${r.files.filter(f=>f.group===g).map(f=>`<div style="margin:3px 0"><a href="${esc(f.href)}" target="_blank" style="color:var(--series-1)">${esc(f.label)}</a> <span class="muted">${f.size}</span></div>`).join('')}</div>`).join('')}
 </div></div>`}

function history(){if(!runs.length)return '';
 const cols=[['area_um2','Area µm²',0,true],['fmax_mhz','Fmax MHz',1,false],['wns_ns','WNS ns',3,false],['power_mw_at_target','Power mW',3,true],['workload_energy_uj','Energy µJ',2,true],['cpi','CPI',2,true]];
 return `<div class="card"><h2>Iterations</h2><div class="scroll"><table><tr><th>#</th><th>tag</th><th>status</th>${cols.map(c=>`<th class="num">${c[1]}</th>`).join('')}<th>knobs changed vs baseline</th></tr>
 ${runs.map((r,i)=>{const p=r.ppa||{}; const ch=base?Object.entries({...r.params,...r.synth_opts}).filter(([k,v])=>({...base.params,...base.synth_opts})[k]!==v).map(([k,v])=>k+'='+v).join(', '):'';
  return `<tr><td>${i}</td><td><code>${esc(r.tag)}</code></td><td><span class="badge ${r.status==='ok'?'ok':r.status==='running'?'run':'bad'}">${esc(r.status)}</span></td>
  ${cols.map(c=>`<td class="num">${fmt(p[c[0]],c[2])}</td>`).join('')}<td class="muted">${esc(ch)||(r===base?'baseline':'—')}</td></tr>`}).join('')}
 </table></div></div>`}

$('#app').innerHTML = header() + pipeline(cur) + summary(cur) + logs(cur) + tiles(last) +
 `<div class="grid g3">${trend('Power','power_mw_at_target','mW',3,true)}${trend('Fmax','fmax_mhz','MHz',1,false)}${trend('Cell area','area_um2','µm²',0,true)}</div>` +
 `<div class="grid g2">${powerBreak(last)}${regBars(last)}</div>` + timing(last||cur) + history();
document.addEventListener('mousemove',e=>{const t=e.target.closest('[data-tip]'); t?showTip(e,t.dataset.tip):hideTip()});
</script></body></html>
"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval", type=int, default=5)
    a = ap.parse_args()
    p = build(refresh=a.interval)
    print(p)
    while a.watch:
        time.sleep(a.interval)
        build(refresh=a.interval)
