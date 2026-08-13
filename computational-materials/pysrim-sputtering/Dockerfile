# Custom Dockerfile for running SRIM/TRIM via pysrim on macOS ARM64.
#
# Strategy: Use the pre-built costrouc/pysrim image if it works on the host
# architecture. If not (ARM64 incompatibility), this Dockerfile builds from
# ubuntu:20.04 with Wine and SRIM installed.
#
# Usage:
#   docker build -t pysrim .
#   docker run -v $(pwd)/output:/app/output pysrim python examples/01_basic_n_on_sio2.py

FROM --platform=linux/amd64 ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV WINEDEBUG=-all
ENV DISPLAY=:99

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    wget \
    xvfb \
    python3 \
    python3-pip \
    cabextract \
    && rm -rf /var/lib/apt/lists/*

# Install Wine
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends wine wine32 wine64 && \
    rm -rf /var/lib/apt/lists/*

# Set up Wine prefix
RUN wineboot --init 2>/dev/null || true

# Download and install SRIM
# SRIM-2013 is the latest public version
RUN mkdir -p /opt/SRIM && \
    cd /opt/SRIM && \
    wget -q "http://www.srim.org/SRIM/SRIM-2013-Std.e" -O SRIM-2013-Std.exe || \
    echo "SRIM download may require manual placement. Copy SRIM files to /opt/SRIM/"

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY . /app
WORKDIR /app

# Set SRIM directory
ENV SRIM_EXECUTABLE_DIRECTORY=/opt/SRIM

# Start Xvfb for headless Wine and run
ENTRYPOINT ["bash", "-c", "Xvfb :99 -screen 0 1024x768x16 &>/dev/null & exec \"$@\"", "--"]
CMD ["python3", "-c", "from srim import TRIM; print('pysrim ready')"]
