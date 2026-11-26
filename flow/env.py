"""Tool paths and a subprocess helper shared by every flow stage."""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
OSS = TOOLS / "oss-cad-suite"
RVGCC_BIN = next((TOOLS).glob("xpack-riscv-none-elf-gcc-*")) / "bin"

DESIGN = ROOT / "design" / "picorv32"
RTL_DIR = DESIGN / "rtl"
TB_DIR = DESIGN / "tb"
FW_DIR = DESIGN / "fw"
CONSTRAINTS = ROOT / "constraints"
LIB = ROOT / "pdk" / "sky130hd" / "sky130_fd_sc_hd__tt_025C_1v80.lib"
RUNS = ROOT / "runs"
BUILD = ROOT / "build"          # shared, cacheable artifacts (firmware, lib cache)


def tool_env() -> dict:
    env = os.environ.copy()
    extra = [str(OSS / "bin"), str(OSS / "lib"), str(RVGCC_BIN)]
    env["PATH"] = os.pathsep.join(extra + [env.get("PATH", "")])
    env["VERILATOR_ROOT"] = str(OSS / "share" / "verilator")
    return env


@dataclass
class CmdResult:
    cmd: list
    returncode: int
    stdout: str
    seconds: float


def run(cmd: list, cwd: Path | None = None, log: Path | None = None,
        timeout: int = 3600, check: bool = True) -> CmdResult:
    t0 = time.time()
    env = tool_env()
    exe = shutil.which(str(cmd[0]), path=env["PATH"]) or str(cmd[0])
    p = subprocess.run([exe] + [str(c) for c in cmd[1:]], cwd=cwd, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors="replace", timeout=timeout)
    res = CmdResult(cmd, p.returncode, p.stdout, time.time() - t0)
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(f"$ {' '.join(map(str, cmd))}\n{p.stdout}", encoding="utf-8")
    if check and p.returncode != 0:
        tail = "\n".join(p.stdout.splitlines()[-40:])
        raise RuntimeError(f"command failed ({p.returncode}): {cmd[0]}\n{tail}")
    return res
