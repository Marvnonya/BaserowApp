FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Systemabhängigkeiten (root)
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv git wget unzip curl build-essential \
    libssl-dev libffi-dev openjdk-17-jdk ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Anlegen des Users (root)
RUN useradd -m builduser

# Vorbereitung der Pfade (root)
RUN mkdir -p /home/builduser/app /usr/local/bin
RUN chown -R builduser:builduser /home/builduser

# Installiere venv und Buildozer als builduser
USER builduser
WORKDIR /home/builduser

RUN python3 -m venv /home/builduser/.venv \
    && /home/builduser/.venv/bin/pip install --upgrade pip setuptools wheel \
    && /home/builduser/.venv/bin/pip install buildozer==1.5.0 Cython==0.29.36 kivy==2.3.1

# <-- NEUER BLOCK: preinstall P4A / buildozer runtime deps in venv (wichtig)
RUN /home/builduser/.venv/bin/pip install \
    appdirs \
    colorama>=0.3.3 \
    jinja2 \
    "sh>=1.10,<2.0" \
    build \
    toml \
    packaging \
    setuptools \
    wheel || true

# Stelle sicher, dass venv bin in PATH ist (für non-root execution)
ENV PATH="/home/builduser/.venv/bin:${PATH}"

# Zurück zu root um entrypoint zu kopieren und Rechte anzupassen
USER root

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && chown root:root /usr/local/bin/entrypoint.sh

WORKDIR /home/builduser/app

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["buildozer", "android", "debug"]
