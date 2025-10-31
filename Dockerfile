# Basis-Image
FROM ubuntu:22.04

# Non-root User erstellen
RUN useradd -ms /bin/bash builduser
USER builduser
WORKDIR /home/builduser

# Systemabhängigkeiten
RUN sudo apt-get update && sudo apt-get install -y \
    python3 python3-pip python3-venv git wget unzip openjdk-17-jdk \
    curl build-essential libssl-dev libffi-dev && \
    sudo rm -rf /var/lib/apt/lists/*

# Python-Umgebung
RUN python3 -m venv /home/builduser/.venv
ENV PATH="/home/builduser/.venv/bin:$PATH"

# Buildozer und Kivy installieren
RUN pip install --upgrade pip
RUN pip install buildozer==1.4.3 Cython==0.29.36 kivy==2.3.2

# Android SDK / NDK vorbereiten
ENV ANDROID_HOME=/home/builduser/android-sdk
RUN mkdir -p $ANDROID_HOME
# SDK + Build Tools
RUN yes | sdkmanager --licenses || true

# Arbeitsverzeichnis für Builds
WORKDIR /home/builduser/app

# Buildozer Allow Root (optional, sicherheitshalber)
ENV BUILDOZER_ALLOW_ROOT=1
