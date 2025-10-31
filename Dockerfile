FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Systemabhängigkeiten
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv git wget unzip curl build-essential \
    libssl-dev libffi-dev openjdk-17-jdk \
    && rm -rf /var/lib/apt/lists/*

# User anlegen
RUN useradd -m builduser
USER builduser
WORKDIR /home/builduser

# Python venv und Buildozer installieren
RUN python3 -m venv .venv
RUN .venv/bin/pip install --upgrade pip
RUN .venv/bin/pip install buildozer==1.5.0 Cython==0.29.36 kivy==2.3.1

# Arbeitsverzeichnis App
WORKDIR /home/builduser/app
RUN mkdir -p /home/builduser/app/.buildozer

# PATH für venv
ENV PATH="/home/builduser/.venv/bin:$PATH"
