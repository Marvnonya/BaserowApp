# Dockerfile
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH

# --- Systemabhängigkeiten (root) ---
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv git wget unzip curl build-essential \
    libssl-dev libffi-dev openjdk-17-jdk ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Non-root user anlegen (root) ---
RUN useradd -m builduser

# Arbeitsverzeichnisse vorbereiten (root)
RUN mkdir -p /home/builduser/app /usr/local/bin
RUN chown -R builduser:builduser /home/builduser

# Wechsel zu builduser, installiere venv & Buildozer in dessen Heimat
USER builduser
WORKDIR /home/builduser

# Python venv und Pakete (installiert für builduser)
RUN python3 -m venv /home/builduser/.venv \
    && /home/builduser/.venv/bin/pip install --upgrade pip setuptools wheel \
    && /home/builduser/.venv/bin/pip install buildozer==1.5.0 Cython==0.29.36 kivy==2.3.1

# PATH so setzen, dass buildozer aus venv verfügbar ist
ENV PATH="/home/builduser/.venv/bin:${PATH}"

# Zurück zu root, um entrypoint in /usr/local/bin zu copy/chmod zu können
USER root

# --- Entrypoint kopieren & ausführbar machen (root) ---
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && chown root:root /usr/local/bin/entrypoint.sh

# Arbeitsverzeichnis final
WORKDIR /home/builduser/app

# Default ENTRYPOINT/CMD, ENTRYPOINT regelt user+chown, CMD ist Default build command
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["buildozer", "android", "debug"]
