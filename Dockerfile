# Dockerfile — Buildozer image mit vorinstallierten p4a-deps in venv
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# System-Pakete (root)
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv git wget unzip curl build-essential \
    libssl-dev libffi-dev openjdk-17-jdk ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Neuen User anlegen
RUN useradd -m builduser

# Prepare folders (root) und owner setzen
RUN mkdir -p /home/builduser/app /usr/local/bin \
 && chown -R builduser:builduser /home/builduser

# Wechsel zu builduser und installiere venv + buildozer + p4a deps in der venv
USER builduser
WORKDIR /home/builduser

RUN python3 -m venv /home/builduser/.venv \
 && /home/builduser/.venv/bin/pip install --upgrade pip setuptools wheel \
 && /home/builduser/.venv/bin/pip install buildozer==1.5.0 Cython==0.29.36 kivy==2.3.1 \
 && /home/builduser/.venv/bin/pip install --no-cache-dir \
    appdirs \
    "colorama>=0.3.3" \
    jinja2 \
    "sh>=1.10,<2.0" \
    build \
    toml \
    packaging \
    setuptools \
    wheel \
    requests \
    pyparsing \
    importlib_metadata || true

# PATH so that venv binaries are available
ENV PATH="/home/builduser/.venv/bin:${PATH}"

# Zurück zu root, um entrypoint zu kopieren und Rechte zu setzen
USER root

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && chown root:root /usr/local/bin/entrypoint.sh

WORKDIR /home/builduser/app

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["buildozer", "android", "debug"]
