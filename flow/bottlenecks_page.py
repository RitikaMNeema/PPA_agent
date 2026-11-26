"""HTML template for runs/bottlenecks.html (built by dashboard.build_bottlenecks)."""

BTEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PPA Bottlenecks</title>
<style>/*__STYLE__*/
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}
.tab{flex:1 1 200px;background:var(--surface-1);border:1px solid var(--border);border-radius:8px;padding:8px 14px;cursor:pointer;font:inherit;font-size:12px;color:var(--text-secondary);text-align:left}
.tab b{display:block;color:var(--text-primary);font-size:14px}
.tab[aria-selected="true"]{border-color:var(--series-1);box-shadow:inset 0 -3px 0 var(--series-1)}
.bn{display:grid;grid-template-columns:36px minmax(120px,1.2fr) minmax(60px,1fr) 110px;gap:8px;align-items:center;padding:7px 4px;border-bottom:1px solid var(--grid)}
.bn .id{font-weight:600;color:var(--text-secondary);font-size:12px}
.bn .det{grid-column:2/-1;color:var(--text-secondary);font-size:12px;margin-top:-4px}
.bn.hl{background:var(--chip);border-radius:6px}
.bar{height:10px;background:var(--grid);border-radius:4px}.bar>div{height:10px;border-radius:4px}
.sg{border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:12px}
.sg h3{margin:0 0 6px;font-size:14px;font-weight:600}
.sg .meta{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
.sg p{margin:6px 0;color:var(--text-secondary)}
.sg pre,.bn pre{background:var(--bg);border:1px solid var(--grid);border-radius:6px;padding:8px;white-space:pre-wrap;word-break:break-word;max-height:none;color:var(--text-primary)}
.imp{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin:8px 0}
.imp div{background:var(--bg);border-radius:6px;padding:6px 8px;font-size:12px}
.imp b{display:block;font-size:11px;color:var(--text-muted);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.banner{border-radius:10px;padding:10px 14px;margin-bottom:16px;border:1px solid var(--border);background:var(--surface-1)}
.banner.ai{border-left:4px solid var(--series-1)} .banner.rules{border-left:4px solid var(--warning)}
details summary{cursor:pointer;color:var(--series-1);font-size:12px;margin-top:4px}
.seg{display:inline-flex;border:1px solid var(--border);border-radius:6px;overflow:hidden}
.seg button{background:var(--surface-1);border:0;padding:3px 10px;font:inherit;font-size:12px;color:var(--text-secondary);cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--chip);color:var(--text-primary);font-weight:600}
.seg button:disabled{opacity:.45;cursor:not-allowed}
select{font:inherit;font-size:12px;background:var(--surface-1);color:var(--text-primary);border:1px solid var(--border);border-radius:4px}
pre.diff{padding:0;overflow:auto;max-height:420px;white-space:pre}
pre.diff span{display:block;padding:0 8px}
pre.diff .add{background:color-mix(in srgb,var(--good) 16%,transparent)}
pre.diff .del{background:color-mix(in srgb,var(--critical) 16%,transparent)}
pre.diff .hunk{color:var(--text-muted);background:var(--chip)}
.pick{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--text-secondary);cursor:pointer;margin-left:auto}
.pick input{width:16px;height:16px;accent-color:var(--series-1)}
.sg.sel{border-color:var(--series-1);box-shadow:0 0 0 1px var(--series-1)}
.sgh{display:flex;gap:8px;align-items:flex-start}
.actbar{position:sticky;bottom:12px;z-index:5;display:flex;flex-wrap:wrap;gap:10px;align-items:center;background:var(--surface-1);border:1px solid var(--series-1);border-radius:10px;padding:10px 14px;box-shadow:0 6px 24px rgba(0,0,0,.18);margin-top:8px}
.btn{background:var(--series-1);color:#fff;border:0;border-radius:6px;padding:7px 14px;font:inherit;font-weight:600;cursor:pointer}
.btn:disabled{opacity:.45;cursor:not-allowed}
.btn.ghost{background:var(--chip);color:var(--text-primary);border:1px solid var(--border)}
.note{font-size:12px;color:var(--text-secondary)}
</style></head>
<body><div class="wrap" id="app"></div><div class="tip" id="tip"></div>
<script>
const D=/*__DATA__*/;
try{const t=localStorage.getItem('ppa-theme'); if(t) document.documentElement.dataset.theme=t;}catch(e){}
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(v,d=1)=>v==null?'–':Number(v).toLocaleString(undefined,{maximumFractionDigits:d,minimumFractionDigits:d});
const get=(k,d)=>{try{return localStorage.getItem(k)||d}catch(e){return d}}, put=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const CATS=[['power','Power'],['timing','Timing'],['congestion','Congestion']];
const S={tag:get('bn-tag',null),cat:get('bn-cat','power'),src:get('bn-src','llm')};
window.flip=()=>{const r=document.documentElement;const dark=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
 r.dataset.theme=dark?'light':'dark';put('ppa-theme',r.dataset.theme)};
const tip=$('#tip');
document.addEventListener('mousemove',e=>{const t=e.target.closest('[data-tip]'); if(t){tip.innerHTML=t.dataset.tip;tip.style.display='block';
 tip.style.left=Math.min(e.clientX+14,innerWidth-tip.offsetWidth-8)+'px';tip.style.top=(e.clientY+14)+'px'}else tip.style.display='none'});
window.hl=(ids,on)=>ids.split(',').forEach(i=>{const e=document.getElementById('bn-'+i); if(e)e.classList.toggle('hl',!!on)});
window.setS=(k,v)=>{S[k]=v;put('bn-'+k,v);render()};

function headline(cat,b){const p=b.ppa||{};
 if(cat==='power')return b.power.available?`${fmt(b.power.total_mw,2)} mW · ${fmt(b.power.clock_share_pct,0)}% clock`:'no power data';
 if(cat==='timing')return `WNS ${fmt(p.wns_ns,3)} ns · Fmax ${fmt(p.fmax_mhz,1)} MHz`;
 return b.congestion.available?`${fmt(b.congestion.avg_pin_density,2)} pins/µm² avg (proxy)`:'no netlist'}

function bnRow(tag,it,mx){const r=it.rtl||{}; const neg=it.unit.includes('slack')||it.unit.includes('WNS');
 const val=neg?`<span style="color:var(${it.metric<0?'--critical-text':'--good-text'})">${fmt(it.metric,3)}</span>`:fmt(it.metric,it.unit==='mW'?3:0);
 const w=neg?100*Math.abs(Math.min(it.metric,0))/mx:100*it.metric/mx;
 const lines=(r.assign_lines||[]).slice(0,3).join(',')||r.decl_line||'?';
 const loc=r.file?`<a href="${esc(tag)}/inputs/${esc(r.file)}" target="_blank" style="color:var(--series-1)">${esc(r.file)}:${lines}</a>`:'';
 return `<div class="bn" id="bn-${it.id}">
  <span class="id">${it.id}</span><code style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(it.full_name||it.name)}">${esc(it.name)}</code>
  <div class="bar" data-tip="<b>${esc(it.name)}</b><br>${esc(it.detail)}"><div style="width:${Math.max(2,Math.min(100,w))}%;background:var(${neg?'--critical':'--series-1'})"></div></div>
  <span style="text-align:right;font-variant-numeric:tabular-nums">${val} <span class="muted">${esc(it.unit)}</span></span>
  <div class="det">${esc(it.detail)}${it.share_pct!=null?` · ${fmt(it.share_pct,1)}% of total`:''}${loc?' · '+loc:''}
  ${r.note?`<div><i>${esc(r.note)}</i></div>`:''}
  ${r.snippet?`<details><summary>RTL · ${esc(r.module)} · <code>${esc(r.rtl_name)}</code></summary><pre>${esc(r.snippet)}</pre></details>`:''}</div></div>`}

// ---- selection / server state ----
const SEL=new Set(); let SERVER=false, BUSY=null, RESULT=null, MSG='';
function diffHtml(d){return `<pre class="diff">${d.split('\n').filter((l,i,a)=>i<a.length-1||l).map(l=>{
 const c=l.startsWith('+++')||l.startsWith('---')?'hunk':l.startsWith('@@')?'hunk':l.startsWith('+')?'add':l.startsWith('-')?'del':'';
 return `<span class="${c}">${esc(l)||' '}</span>`}).join('')}</pre>`}
function rtlBlock(s){const p=s._preview||{}; const pv=D.patch_verify||{};
 if(!p.ok)return `<div class="note" style="margin-top:6px">⚙ No automatic RTL patch yet${p.reason&&p.reason!=='no automatic patch'?': '+esc(p.reason):''}${s.kind==='synth_knob'?' — needs a synthesis-flow knob (phase 2).':' — manual / needs flow support for clock gating.'}</div>`;
 const v=s.patch_id&&pv[s.patch_id]; const add=(p.diff.match(/^\+(?!\+\+)/mg)||[]).length, del=(p.diff.match(/^-(?!--)/mg)||[]).length;
 const par=Object.entries(p.params||{}).map(([k,x])=>`<code>${esc(k)}: ${esc(x)}</code>`).join(' ');
 return `<details ${S.open?'open':''}><summary><b>Suggested new RTL</b> · ${p.diff?`+${add} / −${del} lines`:'parameter change only'}${par?' · '+par:''}
  ${v?` · <span style="color:var(${v.sim_pass&&v.lint_ok?'--good-text':'--critical-text'})">${v.sim_pass&&v.lint_ok?'✓ lint + firmware regression pass':'✗ regression failed'} (${fmt(v.cycles,0)} cycles)</span>`:' · <span class="muted">not yet regression-checked</span>'}</summary>
  ${p.diff?diffHtml(p.diff):''}</details>`}
window.pick=(k,on)=>{on?SEL.add(k):SEL.delete(k);render()};

function card(s,cat,i){const risk={low:'ok',medium:'',high:'bad'}[s.functional_risk]||''; const ids=esc(s.bottleneck_ids.join(','));
 const key=cat+':'+i, can=(s._preview||{}).ok;
 return `<div class="sg ${SEL.has(key)?'sel':''}" onmouseenter="hl('${ids}',1)" onmouseleave="hl('${ids}',0)">
 <div class="sgh"><h3>${esc(s.title)}</h3>${can?`<label class="pick"><input type="checkbox" ${SEL.has(key)?'checked':''} onchange="pick('${key}',this.checked)">use in next iteration</label>`:''}</div>
 <div class="meta"><span class="badge">${esc(s.kind.replace('_',' '))}</span><span class="badge ${risk}">functional risk: ${esc(s.functional_risk)}</span>
 <span class="badge">confidence: ${esc(s.confidence)}</span>${s.rtl_location&&s.rtl_location!=='n/a'?`<span class="badge"><code>${esc(s.rtl_location)}</code></span>`:''}
 ${s.bottleneck_ids.length?`<span class="badge">addresses ${esc(s.bottleneck_ids.join(', '))}</span>`:''}</div>
 <p>${esc(s.rationale)}</p><pre>${esc(s.change)}</pre>
 <div class="imp"><div><b>Power</b>${esc(s.expected_power)}</div><div><b>Timing</b>${esc(s.expected_timing)}</div><div><b>Area</b>${esc(s.expected_area)}</div></div>
 <div class="muted">✓ verify: ${esc(s.verification)}</div>${rtlBlock(s)}</div>`}

// ---- generate / run ----
window.generate=async()=>{const pg=curPage(); MSG='generating candidate + lint …'; BUSY='gen'; render();
 try{const r=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({tag:pg.tag,source:curSrc(),keys:[...SEL]})}); const j=await r.json();
   if(!r.ok||j.error){MSG='✗ '+(j.error||r.status);RESULT=null}else{RESULT=j;MSG='';SEL.clear();await loadCands()}}
 catch(e){MSG='✗ '+e}
 BUSY=null; render(); const el=document.getElementById('result'); if(el)el.scrollIntoView({behavior:'smooth'})};
window.runCand=async(name)=>{const pc=+document.getElementById('pc-'+name).value; BUSY='run'; render();
 try{const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,pwr_cycles:pc})});
   const j=await r.json(); MSG=j.error?'✗ '+j.error:`▶ started <code>${esc(name)}</code> — follow it live on the <a href="dashboard.html" target="_blank" style="color:var(--series-1)">PPA dashboard</a>`;
   await loadCands()}catch(e){MSG='✗ '+e}
 BUSY=null; render()};
async function loadCands(){try{const r=await fetch('/api/candidates'); D.candidates=(await r.json()).candidates}catch(e){}}
const PWR=`<option value="100000">gate-level power: 100k-cycle window (~3 min)</option><option value="0">gate-level power: full workload (~40 min)</option><option value="-1">skip power (lint, sim, synth, STA only)</option>`;
function runCtl(name){return SERVER?`<select id="pc-${esc(name)}">${PWR}</select> <button class="btn" ${BUSY?'disabled':''} onclick="runCand('${esc(name)}')">▶ Run next iteration</button>`:''}
function resultCard(){if(!RESULT)return '';const m=RESULT, l=m.lint||{};
 return `<div class="card" id="result" style="border-color:var(--series-1)"><h2>New RTL generated · <code>${esc(m.name)}</code>
  <span class="badge ${l.ok?'ok':'bad'}">${l.ok?'✓ lint clean':'✗ lint errors: '+l.errors}</span> <span class="muted" style="font-weight:400">${fmt(l.warnings,0)} warnings · from ${esc(m.base_run)} · ${esc(m.source)} advice</span></h2>
  <div class="note">applied: ${m.applied.map(esc).join(' · ')}${Object.keys(m.param_changes||{}).length?' · params '+esc(JSON.stringify(m.param_changes)):''}</div>
  <div class="note" style="margin:6px 0">files: <code>design/picorv32/candidates/${esc(m.name)}/</code> (picorv32.v, config.json, patch.diff) · CLI: <code>${esc(m.next_command)}</code></div>
  ${m.diff?diffHtml(m.diff):''}
  <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">${runCtl(m.name)}<button class="btn ghost" onclick="RESULT=null;render()">close</button></div></div>`}
function candCard(){const C=(D.candidates||[]); if(!C.length)return '';
 return `<div class="card"><h2>Generated RTL candidates <span class="muted" style="font-weight:400">· design/picorv32/candidates/</span></h2><div class="scroll"><table>
 <tr><th>candidate</th><th>from</th><th>changes</th><th>lint</th><th>flow run</th><th></th></tr>
 ${C.slice().reverse().map(c=>`<tr><td><code>${esc(c.name)}</code><div class="muted">${esc(c.created)}</div></td><td><code>${esc(c.base_run)}</code></td>
  <td style="white-space:normal">${c.applied.map(esc).join('<br>')}${SERVER?` · <a href="/candidates/${esc(c.name)}/patch.diff" target="_blank" style="color:var(--series-1)">diff</a>`:''}</td>
  <td>${c.lint?`<span class="badge ${c.lint.ok?'ok':'bad'}">${c.lint.ok?'✓':'✗'}</span>`:'–'}</td>
  <td>${c.run_status?`<span class="badge ${c.run_status==='ok'?'ok':c.run_status==='running'?'run':'bad'}">${esc(c.run_status)}</span>`:'<span class="muted">not run</span>'}</td>
  <td>${!c.run_status||c.run_status.startsWith('fail')?runCtl(c.name):''}</td></tr>`).join('')}</table></div></div>`}
function actBar(){const n=SEL.size;
 return `<div class="actbar"><b>${n} change${n===1?'':'s'} selected</b>
  ${SERVER?`<button class="btn" ${!n||BUSY?'disabled':''} onclick="generate()">⚙ Generate new RTL for next iteration</button>
   ${n?`<button class="btn ghost" onclick="SEL.clear();render()">clear</button>`:''}`
  :`<span class="note">Buttons need the local flow server: run <code>python flow/serve.py</code> and open <a href="http://127.0.0.1:8765/bottlenecks.html" style="color:var(--series-1)">http://127.0.0.1:8765/bottlenecks.html</a> (a page opened as a file cannot run the flow).</span>`}
  ${MSG?`<span class="note" style="flex-basis:100%">${MSG}</span>`:''}</div>`}
let curPage=()=>null, curSrc=()=>'rules';

function render(){
 if(!D.pages.length){$('#app').innerHTML='<div class="card empty">No completed run yet.</div>';return}
 const pg=D.pages.find(p=>p.tag===S.tag)||D.pages[D.pages.length-1];
 const b=pg.bottlenecks, hasAI=!!pg.llm, src=hasAI&&S.src==='llm'?'llm':'rules', adv=src==='llm'?pg.llm:pg.rules;
 const cat=CATS.some(c=>c[0]===S.cat)?S.cat:'power', B=b[cat], A=adv[cat]||{suggestions:[]};
 const mx={}; B.items.forEach(i=>mx[i.unit]=Math.max(mx[i.unit]||0,Math.abs(i.metric))||1);
 const meta=hasAI?(pg.llm._meta||{}):{};
 curPage=()=>pg; curSrc=()=>src;
 $('#app').innerHTML=resultCard()+`<header><h1>Bottlenecks &amp; AI feedback · PicoRV32</h1>
  <span class="sub">top bottlenecks per category, anchored to RTL lines, with recommended RTL / knob changes</span>
  <a class="toggle" style="text-decoration:none" href="dashboard.html">← PPA dashboard</a><button class="toggle" style="margin-left:0" onclick="flip()">theme</button>
  <div class="muted" style="flex-basis:100%">run <select onchange="setS('tag',this.value)">${D.pages.map(p=>`<option ${p.tag===pg.tag?'selected':''}>${esc(p.tag)}</option>`).join('')}</select>
  · analysed ${esc(pg.generated)} · page built ${esc(D.generated)}</div></header>
 <div class="banner ${src==='llm'?'ai':'rules'}" style="display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center">
  <span class="seg"><button aria-pressed="${src==='llm'}" ${hasAI?'':'disabled title="no AI advice for this run yet"'} onclick="setS('src','llm')">AI (Claude)</button>
  <button aria-pressed="${src==='rules'}" onclick="setS('src','rules')">Rule-based</button></span>
  ${src==='llm'?`<span><b>AI feedback</b> · ${esc(meta.model||'claude')} · ${fmt(meta.input_tokens,0)} in / ${fmt(meta.output_tokens,0)} out tokens · ${fmt(meta.seconds,0)} s</span>`
   :`<span><b>Rule-based draft</b> — deterministic pattern → fix table, no LLM.${hasAI?'':` AI feedback not generated yet${pg.llm_error?` (<span class="muted">${esc(pg.llm_error)}</span>)`:''} — run <code>python flow/advisor.py --tag ${esc(pg.tag)}</code>`}</span>`}
  <div style="flex-basis:100%;color:var(--text-secondary)">${esc(adv.overall_summary||'')}</div>
  ${(adv.next_iteration_plan||[]).length?`<div style="flex-basis:100%" class="muted">next-iteration plan: ${adv.next_iteration_plan.map((t,i)=>`<b style="color:var(--text-primary)">${i+1}.</b> ${esc(t)}`).join(' &nbsp; ')}</div>`:''}
 </div>
 <div class="tabs" role="tablist">${CATS.map(([k,l])=>`<button class="tab" role="tab" aria-selected="${k===cat}" onclick="setS('cat','${k}')">
   <b>${l}</b>${esc(headline(k,b))} · ${b[k].items.length} bottlenecks · ${(adv[k]||{suggestions:[]}).suggestions.length} fixes</button>`).join('')}</div>
 <div class="grid g2">
  <div class="card"><h2>Top ${CATS.find(c=>c[0]===cat)[1].toLowerCase()} bottlenecks</h2>
   <div class="muted" style="margin-bottom:8px">${esc(B.summary||'')}${B.proxy?'<br><b>Proxy:</b> no placement in this flow yet — ranked by netlist logic-cone pin density and net fanout.':''}</div>
   ${B.items.length?B.items.map(it=>bnRow(pg.tag,it,mx[it.unit])).join(''):'<div class="empty">no data for this run</div>'}
   ${cat==='timing'&&B.startpoint_groups?`<div class="muted" style="margin-top:10px">worst startpoints: ${B.startpoint_groups.map(s=>`<code>${esc(s.name)}</code> ${fmt(s.wns_ns,3)}`).join(' · ')}</div>`:''}
  </div>
  <div class="card"><h2>${src==='llm'?'AI':'Rule-based'} RTL feedback <span class="muted" style="font-weight:400">· hover a card to highlight the bottlenecks it addresses</span></h2>
   <div class="muted" style="margin-bottom:10px">${esc(A.diagnosis||'')}</div>
   ${A.suggestions.length?A.suggestions.map((s,i)=>card(s,cat,i)).join(''):'<div class="empty">no suggestions</div>'}</div>
 </div>`+candCard()+actBar();
 if(RESULT){const h=$('#app'), r=$('#result'); h.prepend(r)}}
window.setS=(k,v)=>{if(k==='tag'||k==='src')SEL.clear();S[k]=v;put('bn-'+k,v);render()};
render();
if(location.protocol.startsWith('http'))fetch('/api/ping').then(r=>r.json()).then(j=>{SERVER=!!j.ok;render()}).catch(()=>{});
// light auto-refresh (keeps the page in sync with the flow) unless the user is mid-selection
setInterval(()=>{if(!SEL.size&&!RESULT&&!BUSY)location.reload()},60000);
</script></body></html>
"""
