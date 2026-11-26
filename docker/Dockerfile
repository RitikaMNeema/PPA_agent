# PPA_agent image: EDA toolchain + Python + Spark, used for
#   * the flow itself (hermetic, reproducible tool versions)
#   * Spark master / worker nodes (every worker must be able to run the flow)
#   * the driver (DSE optimiser or agent loop)
#
#   docker build -t ppa-agent -f docker/Dockerfile .
FROM python:3.12-slim-bookworm

ARG OSS_CAD_DATE=2025-11-25
ARG RVGCC_VER=15.2.0-1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl xz-utils procps openjdk-17-jre-headless make \
    && rm -rf /var/lib/apt/lists/*

# OSS CAD Suite (Yosys, ABC, Icarus Verilog, Verilator, eqy) + xPack RISC-V GCC
ENV PPA_TOOLS=/opt/eda
RUN mkdir -p $PPA_TOOLS && cd $PPA_TOOLS \
    && curl -fsSL "https://github.com/YosysHQ/oss-cad-suite-build/releases/download/${OSS_CAD_DATE}/oss-cad-suite-linux-x64-$(echo ${OSS_CAD_DATE} | tr -d -).tgz" | tar xz \
    && curl -fsSL "https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack/releases/download/v${RVGCC_VER}/xpack-riscv-none-elf-gcc-${RVGCC_VER}-linux-x64.tar.gz" | tar xz

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Spark standalone scripts ship inside the pyspark wheel
ENV SPARK_HOME=/usr/local/lib/python3.12/site-packages/pyspark \
    PYSPARK_PYTHON=python3 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/work/flow
ENV PATH=$SPARK_HOME/bin:$PATH

# The repository is mounted at /work (shared volume = the farm's shared filesystem)
WORKDIR /work
CMD ["python3", "flow/run_flow.py", "--help"]
