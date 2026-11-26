"""Build the PicoRV32 self-checking firmware (riscv-tests ISA suite + sieve,
multiply test, IRQ test) into a hex image for $readmemh.

Mirrors the upstream Makefile, but runs natively on Windows with the xPack GCC.
The firmware is the *golden workload*: it is the same for every design
iteration, so it is built once and cached.
"""
from __future__ import annotations

from pathlib import Path

from env import BUILD, FW_DIR, run

PREFIX = "riscv-none-elf-"
# GCC >= 12 split CSR instructions out of the base ISA -> add _zicsr.
MARCH_C = "rv32ic_zicsr"
MARCH_ASM = "rv32imc_zicsr"
FW_OBJS = ["start", "irq", "print", "hello", "sieve", "multest", "stats"]


def build_firmware(force: bool = False) -> Path:
    out = BUILD / "firmware"
    hexf = out / "firmware.hex"
    if hexf.exists() and not force:
        return hexf
    out.mkdir(parents=True, exist_ok=True)
    objs = []
    for name in FW_OBJS:
        src = FW_DIR / (name + (".S" if name == "start" else ".c"))
        obj = out / f"{name}.o"
        if src.suffix == ".S":
            run([PREFIX + "gcc", "-c", "-mabi=ilp32", f"-march={MARCH_ASM}", "-o", obj, src])
        else:
            run([PREFIX + "gcc", "-c", "-mabi=ilp32", f"-march={MARCH_C}", "-Os", "--std=c99",
                 "-Wall", "-ffreestanding", "-nostdlib", "-o", obj, src])
        objs.append(obj)
    for s in sorted((FW_DIR / "tests").glob("*.S")):
        t = s.stem
        obj = out / f"test_{t}.o"
        run([PREFIX + "gcc", "-c", "-mabi=ilp32", f"-march={MARCH_ASM}", "-o", obj,
             f"-DTEST_FUNC_NAME={t}", f'-DTEST_FUNC_TXT="{t}"', f"-DTEST_FUNC_RET={t}_ret", s])
        objs.append(obj)
    elf = out / "firmware.elf"
    run([PREFIX + "gcc", "-Os", "-mabi=ilp32", f"-march={MARCH_ASM}", "-ffreestanding", "-nostdlib",
         "-o", elf, f"-Wl,--build-id=none,-Bstatic,-T,{FW_DIR / 'sections.lds'},--strip-debug",
         *objs, "-lgcc"])
    binf = out / "firmware.bin"
    run([PREFIX + "objcopy", "-O", "binary", elf, binf])
    data = binf.read_bytes()
    words = 32768
    assert len(data) <= 4 * words, "firmware too large"
    data += b"\0" * (4 * words - len(data))
    hexf.write_text("".join(f"{int.from_bytes(data[i:i+4], 'little'):08x}\n"
                            for i in range(0, len(data), 4)))
    return hexf


if __name__ == "__main__":
    print(build_firmware(force=True))
