FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH

# Systemabhängigkeiten (root)
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv git wget unzip curl build-essential \
    libssl-dev libffi-dev openjdk-17-jdk \
    && rm -rf /var/lib/apt/lists/*

# Non-root User anlegen (root)
RUN useradd -m builduser

# Arbeitsverzeichnis vorbereiten (root)
RUN mkdir -p /home/builduser/app
# (optional) ensure /usr/local/bin exists
RUN mkdir -p /usr/local/bin

# Wechsel zu builduser um venv & pip-User-Install durchzuführen
USER builduser
WORKDIR /home/builduser

# Venv und Buildozer als builduser installieren (keine Root-Warnung später)
RUN python3 -m venv /home/builduser/.venv \
    && /home/builduser/.venv/bin/pip install --upgrade pip \
    && /home/builduser/.venv/bin/pip install buildozer==1.5.0 Cython==0.29.36 kivy==2.3.1

ENV PATH="/home/builduser/.venv/bin:${PATH}"

# Zurück zu root, damit wir entrypoint in /usr/local/bin kopieren und chmod setzen dürfen
USER root

# Copy entrypoint und setze Rechte (als root)
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && chown root:root /usr/local/bin/entrypoint.sh

# Optional: Eintrag für den builduser als Besitzer von /home/builduser/app
RUN chown -R builduser:builduser /home/builduser/app || true

# ENTRYPOINT & Default CMD
# ENTRYPOINT als root ausführbar, das Script wechselt selbst auf builduser (siehe entrypoint)
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["buildozer", "android", "debug"]

# Falls du möchtest, am Ende wieder USER builduser setzen (nicht zwingend nötig)
# USER builduser
