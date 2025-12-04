# Dockerfile for iSIP - Cross-platform SIP Testing
# This enables running iSIP on Linux/Docker instead of Mac-only

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    pkg-config \
    libasound2-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Build PJSIP from source (cross-platform)
WORKDIR /tmp
RUN wget https://github.com/pjsip/pjproject/archive/refs/tags/2.16.tar.gz && \
    tar xzf 2.16.tar.gz && \
    cd pjproject-2.16 && \
    ./configure \
        --disable-video \
        --disable-opencore-amr \
        --disable-silk \
        --disable-sound \
        --enable-shared && \
    make dep && \
    make && \
    cd pjsip-apps/src/python && \
    python3 setup.py install && \
    cd /tmp && \
    rm -rf pjproject-2.16 2.16.tar.gz

# Install Python package
WORKDIR /app
COPY sdk/python/pyproject.toml sdk/python/README.md ./
COPY sdk/python/siptester ./siptester

RUN pip install --no-cache-dir -e .

# Create output directory
RUN mkdir -p /app/output

# Environment variables (override with -e or .env)
ENV OPENAI_API_KEY=""
ENV DEEPGRAM_API_KEY=""
ENV ELEVENLABS_API_KEY=""
ENV SIP_USERNAME=""
ENV SIP_PASSWORD=""
ENV SIP_GATEWAY="2g0282esbg2.sip.livekit.cloud"

WORKDIR /app

# Default command
ENTRYPOINT ["siptester"]
CMD ["--help"]

