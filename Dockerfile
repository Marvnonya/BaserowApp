# --- Basisimage ---
FROM ubuntu:22.04

# --- Umgebungsvariablen ---
ENV DEBIAN_FRONTEND=noninteractive
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH

# --- Systemabhängigkeiten ---
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv git wget unzip curl build-essential \
    libssl-dev libffi-dev openjdk-17-jdk \
    && rm -rf /var/lib/apt/lists/*

# --- Non-root User erstellen ---
RUN useradd -m builduser
WORKDIR /home/builduser

# --- Buildozer und Kivy installieren (für builduser) ---
USER builduser
RUN python3 -m venv .venv
RUN . .venv/bin/activate && pip install --upgrade pip
RUN . .venv/bin/activate && pip install buildozer==1.5.0 Cython==0.29.36 kivy==2.3.1

# --- Arbeitsverzeichnis für App ---
WORKDIR /home/builduser/app

# --- EntryPoint optional ---
# ENTRYPOINT ["/bin/bash"]
