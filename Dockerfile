# Basis-Image
FROM ubuntu:22.04

# Systemabhängigkeiten installieren (läuft als root)
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv git wget unzip openjdk-17-jdk \
    curl build-essential libssl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Non-root User erstellen
RUN useradd -ms /bin/bash builduser
USER builduser
WORKDIR /home/builduser

# Python-Umgebung
RUN python3 -m venv /home/builduser/.venv
ENV PATH="/home/builduser/.venv/bin:$PATH"

# Buildozer und Kivy installieren
RUN pip install --upgrade pip
RUN pip install buildozer==1.5.0 Cython==0.29.36 kivy

# Arbeitsverzeichnis für Builds
WORKDIR /home/builduser/app

# Buildozer Allow Root (sicherheitshalber, CI-kompatibel)
ENV BUILDOZER_ALLOW_ROOT=1
