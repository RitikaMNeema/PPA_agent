"""Distributed job execution for flow runs.

A *job* is one complete flow iteration (lint -> RTL sim -> synth -> STA -> GLS/power)
described by a plain JSON-serialisable dict, so the same job can be shipped to
any backend:

    local   thread pool on this machine, one subprocess per job        (default)
    spark   Apache Spark: one task per job; local[N] here, spark://host:7077 on a cluster
    docker  each job in a fresh container from the ppa-agent image (hermetic toolchain)

In a design house the flow runs on a compute farm: a scheduler fans independent
runs (configs, corners, candidates) out to big machines with a shared filesystem.
Here every worker sees the same repository (NFS / bind mount), writes its own
runs/<tag>/ directory and returns a small summary to the driver.

    from executor import FlowJob, get_executor
    ex = get_executor("spark", workers=8)
    results = ex.map([FlowJob("dse_007", "runs/dse/configs/dse_007.json", 20000)])
"""
from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class FlowJob:
    tag: str
    config: str | None = None          # path relative to repo root (portable across hosts)
    pwr_cycles: int = 20000            # 0 = full workload, <0 = skip power
    launcher: str = "python"           # python | docker
    image: str = "ppa-agent:latest"
    root: str = str(ROOT)              # repo root as seen by the worker (shared FS)
    timeout_s: int = 7200
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------- worker side
def run_job(job: dict) -> dict:
    """Execute one flow job.  Standard library only, so it ships to Spark executors
    or remote workers without the rest of the package being importable there."""
    root = Path(job["root"])
    tag, n = job["tag"], int(job.get("pwr_cycles", 20000))
    args = ["flow/run_flow.py", "--tag", tag]
    if job.get("config"):
        args += ["--config", job["config"]]
    args += ["--skip-power"] if n < 0 else ["--pwr-cycles", str(n)]

    if job.get("launcher") == "docker":
        cmd = ["docker", "run", "--rm", "-v", f"{root}:/work", "-w", "/work",
               "-e", "PPA_NO_DASHBOARD=1", job.get("image", "ppa-agent:latest"), "python3", *args]
    else:
        cmd = [sys.executable, *args]
    # private scratch dir per job: concurrent yosys/abc processes otherwise collide in the
    # shared temp directory (seen on Windows: ABC output.blif vanishing under 10x parallelism)
    scratch = root / "build" / "scratch" / tag
    scratch.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PPA_NO_DASHBOARD="1", PYTHONUNBUFFERED="1",
               TMP=str(scratch), TEMP=str(scratch), TMPDIR=str(scratch))
    log = root / "runs" / f"{tag}.out"
    log.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        with open(log, "w", encoding="utf-8") as fh:
            rc = subprocess.run(cmd, cwd=root, env=env, stdout=fh, stderr=subprocess.STDOUT,
                                timeout=int(job.get("timeout_s", 7200))).returncode
    except subprocess.TimeoutExpired:
        rc = -9
    out = {"tag": tag, "returncode": rc, "seconds": round(time.time() - t0, 1),
           "host": socket.gethostname(), "worker_pid": os.getpid(), "meta": job.get("meta", {})}
    mp = root / "runs" / tag / "metrics.json"
    if mp.exists():
        m = json.loads(mp.read_text())
        st = m.get("stages", {})
        out.update(status=m.get("status"), ppa=m.get("ppa"), params=m.get("params"),
                   synth_opts=m.get("synth_opts"),
                   rtl_pass=st.get("rtl_sim", {}).get("pass"),
                   lint_ok=st.get("lint", {}).get("ok"))
    else:
        out["status"] = "no_metrics" if rc == 0 else f"crash_rc{rc}"
    return out


# --------------------------------------------------------------------------- driver side
def warm_caches():
    """Build shared, read-only artefacts once on the driver (firmware image, liberty
    cache) so parallel workers never race to create them."""
    sys.path.insert(0, str(ROOT / "flow"))
    from firmware import build_firmware
    from libcache import build_cache
    build_firmware()
    build_cache()


class LocalExecutor:
    name = "local"

    def __init__(self, workers: int = 4):
        self.workers = workers

    def map(self, jobs: list[FlowJob]) -> list[dict]:
        warm_caches()
        with ThreadPoolExecutor(self.workers) as pool:       # the work happens in subprocesses
            return list(pool.map(run_job, [j.to_dict() for j in jobs]))


class DockerExecutor(LocalExecutor):
    """Fan out containers from this host (single big machine with Docker)."""
    name = "docker"

    def __init__(self, workers: int = 4, image: str = "ppa-agent:latest"):
        super().__init__(workers)
        self.image = image

    def map(self, jobs: list[FlowJob]) -> list[dict]:
        for j in jobs:
            j.launcher, j.image = "docker", self.image
        return super().map(jobs)


class SparkExecutor:
    """One Spark task per flow run.

    local mode (this laptop):   master = "local[8]"
    cluster (docker compose):   master = "spark://spark-master:7077", workers are
                                containers built from the same image, repo on a shared volume.
    Each task is CPU-heavy and long (minutes), so we use one partition per job and
    let Spark's scheduler place tasks on free executor cores; failed tasks are retried
    by Spark (spark.task.maxFailures)."""
    name = "spark"

    def __init__(self, workers: int = 4, master: str | None = None, root: str | None = None):
        self.workers = workers
        self.master = master or os.environ.get("SPARK_MASTER") or f"local[{workers}]"
        self.root = root or os.environ.get("PPA_WORKER_ROOT")   # repo path as seen by workers
        self._spark = None

    def session(self):
        if self._spark is None:
            os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
            os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
            # executors must be able to import this module to unpickle run_job
            here = str(Path(__file__).resolve().parent)
            os.environ["PYTHONPATH"] = os.pathsep.join(filter(None, [here, os.environ.get("PYTHONPATH")]))
            from pyspark.sql import SparkSession
            b = (SparkSession.builder.appName("PPA_agent")
                           .master(self.master)
                           .config("spark.task.maxFailures", "2")
                           .config("spark.ui.showConsoleProgress", "false")
                           .config("spark.python.worker.reuse", "false"))
            if os.environ.get("SPARK_DRIVER_HOST"):          # client mode inside docker compose
                b = b.config("spark.driver.host", os.environ["SPARK_DRIVER_HOST"])
            self._spark = b.getOrCreate()
            self._spark.sparkContext.setLogLevel("ERROR")
            if not self.master.startswith("local"):
                # remote executors: ship this module (stdlib-only by design)
                self._spark.sparkContext.addPyFile(str(Path(__file__).resolve()))
        return self._spark

    def map(self, jobs: list[FlowJob]) -> list[dict]:
        warm_caches()
        if self.root:
            for j in jobs:
                j.root = self.root
        sc = self.session().sparkContext
        rdd = sc.parallelize([j.to_dict() for j in jobs], numSlices=max(1, len(jobs)))
        return rdd.map(run_job).collect()

    def stop(self):
        if self._spark is not None:
            self._spark.stop()
            self._spark = None


def get_executor(kind: str = "local", workers: int = 4, **kw):
    if kind == "local":
        return LocalExecutor(workers)
    if kind == "docker":
        return DockerExecutor(workers, kw.get("image", "ppa-agent:latest"))
    if kind == "spark":
        return SparkExecutor(workers, kw.get("master"), kw.get("root"))
    raise ValueError(f"unknown executor {kind!r}")


def host_info() -> dict:
    return {"host": socket.gethostname(), "os": platform.platform(), "cpus": os.cpu_count(),
            "python": platform.python_version()}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="run flow jobs on a backend")
    ap.add_argument("--executor", default="local", choices=["local", "spark", "docker"])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--master")
    ap.add_argument("--pwr-cycles", type=int, default=20000)
    ap.add_argument("--configs", nargs="+", required=True, help="config.json paths (relative to repo)")
    a = ap.parse_args()
    jobs = [FlowJob(Path(c).parent.name if Path(c).name == "config.json" else Path(c).stem, c, a.pwr_cycles)
            for c in a.configs]
    ex = get_executor(a.executor, a.workers, master=a.master)
    for r in ex.map(jobs):
        print(json.dumps({k: r.get(k) for k in ("tag", "status", "seconds", "host", "ppa")}))
