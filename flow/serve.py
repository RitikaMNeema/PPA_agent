"""Local dashboard server: serves runs/ and backs the page buttons.

    python flow/serve.py            ->  http://127.0.0.1:8765/bottlenecks.html

Binds to 127.0.0.1 only.  Endpoints:
  GET  /api/ping
  GET  /api/candidates                         list generated candidates
  POST /api/generate  {tag, source, keys[], name?}   apply selected suggestions -> candidate (+ lint)
  POST /api/run       {name, pwr_cycles}             launch run_flow.py on a candidate (one run at a time)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import dashboard
from candidates import CAND_DIR, PatchError, make_candidate
from env import ROOT, RUNS

PORT = 8765
FLOW = Path(__file__).resolve().parent
NAME_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def list_candidates() -> list[dict]:
    out = []
    for mf in sorted(CAND_DIR.glob("*/meta.json")) if CAND_DIR.exists() else []:
        if mf.parent.name.startswith("_"):
            continue
        m = json.loads(mf.read_text())
        rm = RUNS / m["name"] / "metrics.json"
        m["run_status"] = json.loads(rm.read_text())["status"] if rm.exists() else None
        out.append(m)
    return out


def running() -> str | None:
    for mf in RUNS.glob("*/metrics.json"):
        try:
            if json.loads(mf.read_text())["status"] == "running":
                return mf.parent.name
        except Exception:
            pass
    return None


class H(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *a):
        if "/api/" in (self.path or ""):
            sys.stderr.write("[serve] " + fmt % a + "\n")

    def _json(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def end_headers(self):
        if self.path.endswith(".html"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/ping":
            return self._json({"ok": True, "running": running()})
        if self.path == "/api/candidates":
            return self._json({"candidates": list_candidates()})
        if self.path.startswith("/candidates/"):           # view candidate files
            rel = Path(self.path[len("/candidates/"):].split("?")[0])
            f = (CAND_DIR / rel).resolve()
            if CAND_DIR.resolve() in f.parents and f.is_file():
                b = f.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                return self.wfile.write(b)
            return self._json({"error": "not found"}, 404)
        return super().do_GET()

    def do_POST(self):
        if self.headers.get("Origin") not in (None, f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
            return self._json({"error": "cross-origin request refused"}, 403)
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}")
        except Exception:
            return self._json({"error": "bad json"}, 400)
        try:
            if self.path == "/api/generate":
                return self._json(self.generate(req))
            if self.path == "/api/run":
                return self._json(self.run(req))
        except PatchError as e:
            return self._json({"error": str(e)}, 409)
        except (KeyError, IndexError, ValueError) as e:
            return self._json({"error": f"bad request: {e}"}, 400)
        return self._json({"error": "unknown endpoint"}, 404)

    def generate(self, req):
        tag = req["tag"]
        if not NAME_RE.match(tag) or not (RUNS / tag / "advice.json").exists():
            raise ValueError("unknown run")
        adv = json.loads((RUNS / tag / "advice.json").read_text())[req.get("source", "rules")]
        if not adv:
            raise ValueError("no advice of that source")
        sel = []
        for k in req["keys"]:
            cat, i = k.split(":")
            sel.append(adv[cat]["suggestions"][int(i)])
        name = req.get("name") or None
        if name and not NAME_RE.match(name):
            raise ValueError("bad name")
        m = make_candidate(tag, sel, name)
        m["source"] = req.get("source", "rules")
        return m

    def run(self, req):
        name = req["name"]
        if not NAME_RE.match(name) or not (CAND_DIR / name / "config.json").exists():
            raise ValueError("unknown candidate")
        busy = running()
        if busy:
            return {"error": f"run '{busy}' is still in progress - one run at a time"}
        pc = int(req.get("pwr_cycles", 100000))
        cmd = [sys.executable, str(FLOW / "run_flow.py"), "--tag", name,
               "--config", str(CAND_DIR / name / "config.json")]
        cmd += ["--skip-power"] if pc < 0 else ["--pwr-cycles", str(pc)]
        log = open(RUNS / f"{name}.out", "w")
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(cmd, cwd=FLOW, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        return {"ok": True, "started": name, "command": " ".join(cmd[1:])}


if __name__ == "__main__":
    dashboard.build()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), partial(H, directory=str(RUNS)))
    print(f"serving {RUNS} on http://127.0.0.1:{PORT}/bottlenecks.html", flush=True)
    srv.serve_forever()
