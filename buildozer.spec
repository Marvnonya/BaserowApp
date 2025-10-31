[app]
# App-Name
title = BaserowApp
package.name = baserowapp
package.domain = org.example

# Haupt-Datei
source.main = main.py

# Dateien/Ordner, die mit in die APK sollen
source.include_exts = py,png,jpg,kv,json
# Kein screens-Ordner nötig, da alle Screens in main.py

# Version
version = 0.1

# Anforderungen / Dependencies
requirements = python3,kivy,requests,python-dotenv,cython

# Orientierung
orientation = portrait

# Icon (optional)
# icon.filename = %(source.dir)s/icon.png

# Berechtigungen
android.permissions = INTERNET

# Android SDK / NDK Versionen (optional, können angepasst werden)
# android.api = 33
# android.minapi = 21
# android.sdk = 33
# android.ndk = 25b
# android.ndk_api = 21

[buildozer]
# Log-Level (1 = Fehler, 2 = Info, 3 = Debug)
log_level = 2
warn_on_root = 1

# Pfad für den Build-Output
# bin_dir = bin

# Environment-Variable SHORTLINK aus GitHub Secret wird während des Builds gesetzt
# (Im Workflow: env: SHORTLINK: ${{ secrets.SHORTLINK }})
