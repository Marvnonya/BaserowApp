import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.utils import get_color_from_hex

import requests
import json
import os
import re
from datetime import datetime, date
from dotenv import load_dotenv, set_key


# --- Globale Session ---
session = requests.Session()
ENV_PATH = ".env"
load_dotenv()  # Lädt alle Variablen aus .env ins Environment
SHORTLINK = os.getenv("SHORTLINK")

if SHORTLINK is None:
    raise ValueError("Kein SHORTLINK gesetzt! Bitte Environment-Variable prüfen.")

# ---------------------------------------------------
# 🔹 Hilfsfunktionen
def verify_or_refresh_baserow_url(status_label=None):
    """
    Prüft die BASEROW_URL oder holt sie über den Shortlink neu.
    Entfernt /login, hängt /api/ an und speichert in .env.
    Statusmeldungen optional über status_label ausgeben.
    """
    load_dotenv()
    baserow_url = None
    try:
        # Shortlink immer aufrufen
        r = requests.get(SHORTLINK, timeout=5, allow_redirects=True)
        if r.status_code == 200:
            final_url = r.url
            # Falls URL auf /login endet, entfernen
            if final_url.endswith("/login"):
                final_url = final_url[:-len("/login")]
            # Sicherstellen, dass /api/ am Ende steht
            if not final_url.endswith("/api/"):
                final_url = final_url.rstrip("/") + "/api/"
            baserow_url = final_url
            # Speichern in .env
            set_key(ENV_PATH, "BASEROW_URL", final_url)
            msg = f"[INFO] BASEROW_URL aktualisiert: {final_url}"
            if status_label:
                status_label.text = msg
            print(msg)
        else:
            msg = f"[WARN] Shortlink konnte nicht abgerufen werden (Status {r.status_code})"
            if status_label:
                status_label.text = msg
            print(msg)
    except Exception as e:
        msg = f"[ERROR] Fehler beim Abrufen der URL: {e}"
        if status_label:
            status_label.text = msg
        print(msg)
    
    return baserow_url

def login_to_baserow(status_label=None):
    """Login via API Token"""
    load_dotenv()
    base_url = os.getenv("BASEROW_URL")
    api_token = os.getenv("API_TOKEN")

    if not base_url or not api_token:
        if status_label:
            status_label.text = "[WARN] Keine BASEROW_URL oder API_TOKEN in .env"
        print("[WARN] Keine BASEROW_URL oder API_TOKEN in .env")
        return False

    session.headers.update({"Authorization": f"Token {api_token}"})

    # Testen, ob der Token gültig ist, z.B. GET auf die erste Tabelle
    test_url = f"{base_url}database/rows/table/749/?user_field_names=true"
    try:
        r = session.get(test_url)
        if r.status_code == 200:
            if status_label:
                status_label.text = "[OK] API Token gültig, Login erfolgreich"
            print("[OK] API Token gültig, Login erfolgreich ✅")
            return True
        else:
            if status_label:
                status_label.text = f"[WARN] Token ungültig, Status {r.status_code}"
            print(f"[WARN] Token ungültig, Status {r.status_code} - {r.text}")
            return False
    except Exception as e:
        if status_label:
            status_label.text = f"[ERROR] Fehler beim Token-Test: {e}"
        print(f"[ERROR] Fehler beim Token-Test: {e}")
        return False




# ---------------------------------------------------
# 🔹 Screens
# ---------------------------------------------------
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        load_dotenv()
        api_token = os.getenv("API_TOKEN", "")

        layout = BoxLayout(orientation="vertical", padding=10, spacing=5)

        self.status_label = Label(text="Login erforderlich …", size_hint_y=None, height=30)
        layout.add_widget(self.status_label)

        layout.add_widget(Label(text="API Token"))
        self.token_input = TextInput(text=api_token, multiline=False, password=True)
        layout.add_widget(self.token_input)

        # Button zum Ein-/Ausblenden
        self.toggle_btn = Button(text="👁️ Token anzeigen")
        self.toggle_btn.bind(on_release=self.toggle_token)
        layout.add_widget(self.toggle_btn)

        self.save_cb = CheckBox(active=bool(api_token))
        layout.add_widget(Label(text="Token speichern"))
        layout.add_widget(self.save_cb)

        login_btn = Button(text="Login")
        login_btn.bind(on_release=self.try_login)
        layout.add_widget(login_btn)

        self.add_widget(layout)

        # Auto-Login, falls Token vorhanden
        if api_token:
            Clock.schedule_once(lambda dt: self.try_login(auto=True), 0.1)

    def toggle_token(self, instance):
        self.token_input.password = not self.token_input.password
        self.toggle_btn.text = "👁️ Token verstecken" if not self.token_input.password else "👁️ Token anzeigen"

    def try_login(self, instance=None, auto=False):
        token = self.token_input.text.strip()
        save = self.save_cb.active

        if not token:
            self.status_label.text = "Token fehlt!"
            return

        # Session Header setzen
        session.headers.update({"Authorization": f"Token {token}"})

        # Base URL holen
        load_dotenv()
        base_url = os.getenv("BASEROW_URL")
        if not base_url:
            base_url = verify_or_refresh_baserow_url(self.status_label)

        # Testaufruf: GET auf Tabelle 749, statt /user/me/
        test_url = f"{base_url}database/rows/table/749/?user_field_names=true"
        try:
            r = session.get(test_url, timeout=10)
            if r.status_code == 200:
                self.status_label.text = "Hauptmenü"
                print("[OK] Login erfolgreich mit API Token ✅")
                if save:
                    set_key(".env", "API_TOKEN", token)
                if self.manager:
                    self.manager.current = "main_menu"
            else:
                self.status_label.text = "Login fehlgeschlagen"
                print("[WARN] Login fehlgeschlagen", r.status_code, r.text)
        except Exception as e:
            self.status_label.text = f"Login Fehler: {e}"
            print("[ERROR] Login Exception:", e)



class MainMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=5)

        # Statuslabel initialisieren
        self.status_label = Label(text="Hauptmenü", size_hint_y=None, height=30)
        layout.add_widget(self.status_label)

        # Buttons für Aktionen
        layout.add_widget(Button(text="Probe hinzufügen", on_release=self.add_probe))
        layout.add_widget(Button(text="Probe editieren", on_release=self.edit_probe))
        layout.add_widget(Button(text="Event hinzufügen", on_release=self.add_event))
        layout.add_widget(Button(text="Event editieren", on_release=self.edit_event))
        layout.add_widget(Button(text="Notenstücke hinzufügen", on_release=self.add_sheetmusic))


        # Logout-Button
        logout_btn = Button(text="Logout", on_release=self.logout)
        layout.add_widget(logout_btn)

        self.add_widget(layout)

    def on_pre_enter(self):
        """Label zurücksetzen, wenn MainMenu betreten wird"""
        if hasattr(self, 'status_label'):
            self.status_label.text = "Hauptmenü"

    def add_probe(self, instance):
        self.manager.current = "add_probe"

    def edit_probe(self, instance):
        self.manager.current = "edit_probe"

    def add_event(self, instance):
        Popup(title="Info",
              content=Label(text="Event hinzufügen noch nicht implementiert"),
              size_hint=(0.6, 0.4)).open()

    def edit_event(self, instance):
        Popup(title="Info",
              content=Label(text="Event editieren noch nicht implementiert"),
              size_hint=(0.6, 0.4)).open()

    def add_sheetmusic(self, instance):
        self.manager.current="add_sheet_music"

    def logout(self, instance):
        # Token aus Session entfernen
        session.headers.pop("Authorization", None)
        
        # API_TOKEN in .env löschen
        set_key(".env", "API_TOKEN", "")
        
        print("[INFO] Benutzer ausgeloggt")
        
        # Zurück zum Login-Screen, mit Statusmeldung
        login_screen = self.manager.get_screen("login")
        login_screen.status_label.text = "Erfolgreich ausgeloggt"
        self.manager.current = "login"







class AddProbeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=5)

        self.status_label = Label(text="Neue Probe erstellen", size_hint_y=None, height=30)
        layout.add_widget(self.status_label)

        layout.add_widget(Label(text="Probenname"))
        self.name_input = TextInput(multiline=False)
        layout.add_widget(self.name_input)

        layout.add_widget(Label(text="Datum"))
        self.date_input = TextInput(text=datetime.today().strftime("%Y-%m-%d"), multiline=False)
        layout.add_widget(self.date_input)

        create_btn = Button(text="Probe erstellen")
        create_btn.bind(on_release=self.create_probe)
        layout.add_widget(create_btn)

        back_btn = Button(text="Zurück")
        back_btn.bind(on_release=self.go_back)
        layout.add_widget(back_btn)

        self.add_widget(layout)
        self.prefill_last_probe()

    def prefill_last_probe(self):
        """Ermittelt die letzte normale Probe und zählt die Nummer +1 hoch."""
        try:
            load_dotenv()
            base_url = os.getenv("BASEROW_URL")
            api_token = os.getenv("API_TOKEN")
            if not base_url or not api_token:
                self.status_label.text = "Keine BASEROW_URL oder API_TOKEN vorhanden"
                return

            headers = {"Authorization": f"Token {api_token}"}

            api_url = f"{base_url}database/rows/table/749/?user_field_names=true"
            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code != 200:
                self.status_label.text = f"Fehler beim Abruf: {response.status_code}"
                print("[ERROR] GET rows:", response.text)
                return

            data = response.json().get("results", [])
            proben = [p for p in data if "Probe" in p.get("Name", "") and "Sonder" not in p.get("Name", "")]

            if not proben:
                self.status_label.text = "Keine normalen Proben gefunden"
                return

            proben.sort(key=lambda x: x.get("Datum", ""), reverse=True)
            letzte = proben[0]

            match = re.search(r"(\d+)", letzte.get("Name", ""))
            if match:
                nummer = int(match.group(1)) + 1
                neuer_name = re.sub(r"(\d+)", f"{nummer:03}", letzte["Name"], 1)
            else:
                neuer_name = letzte["Name"] + " 001"

            self.name_input.text = neuer_name
            self.date_input.text = date.today().isoformat()
            self.status_label.text = f"Letzte Probe: {letzte['Name']} → {neuer_name}"
            print(f"[DEBUG] Letzte Probe: {letzte['Name']}, neuer Name: {neuer_name}")

        except Exception as e:
            self.status_label.text = f"Fehler: {e}"
            print("prefill_last_probe ERROR:", e)

    def create_probe(self, instance):
        """Erstellt eine neue Probe, prüft auf Duplikate nach Datum."""
        try:
            load_dotenv()
            base_url = os.getenv("BASEROW_URL")
            api_token = os.getenv("API_TOKEN")
            if not base_url or not api_token:
                self.status_label.text = "Keine BASEROW_URL oder API_TOKEN vorhanden"
                return

            headers = {"Authorization": f"Token {api_token}"}
            name = self.name_input.text.strip()
            datum = self.date_input.text.strip()

            if not name or not datum:
                self.status_label.text = "Name und Datum müssen ausgefüllt sein"
                return

            # API-Endpunkt für Tabelle 749
            api_url = f"{base_url}database/rows/table/749/?user_field_names=true"

            # Prüfen, ob Datum schon existiert
            r_check = requests.get(api_url, headers=headers, timeout=10)
            if r_check.status_code != 200:
                self.status_label.text = f"Fehler beim Abruf bestehender Proben: {r_check.status_code}"
                print("[ERROR] GET rows for create:", r_check.text)
                return

            data = r_check.json().get("results", [])
            exists = any(d.get("Datum") == datum for d in data)
            if exists:
                self.status_label.text = f"⚠ Probe für {datum} existiert bereits"
                Popup(title="Info", content=Label(text=f"Probe für {datum} existiert bereits"), size_hint=(0.6, 0.4)).open()
                return

            # Neue Probe anlegen
            payload = {"Name": name, "Datum": datum}
            r_post = requests.post(api_url, headers=headers, json=payload, timeout=10)
            if r_post.status_code in (200, 201):
                self.status_label.text = f"✅ Probe '{name}' erstellt für {datum}"
                Popup(title="Erfolg", content=Label(text=f"Probe '{name}' erstellt ✅"), size_hint=(0.6, 0.4)).open()
            else:
                self.status_label.text = f"Fehler beim Erstellen: {r_post.status_code}"
                Popup(title="Fehler", content=Label(text=f"Fehler: {r_post.text}"), size_hint=(0.6, 0.4)).open()
                print("[ERROR] POST create row:", r_post.text)

        except Exception as e:
            self.status_label.text = f"Fehler: {e}"
            Popup(title="Fehler", content=Label(text=f"{e}"), size_hint=(0.6, 0.4)).open()
            print("create_probe ERROR:", e)

    def go_back(self, instance):
        self.manager.current = "main_menu"

class EditProbeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=5)

        self.status_label = Label(text="Probe auswählen", size_hint_y=None, height=30)
        layout.add_widget(self.status_label)

        # ScrollView für Probenliste
        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)
        layout.add_widget(self.scroll)

        # Buttons unten
        select_btn = Button(text="Auswählen", size_hint_y=None, height=40)
        select_btn.bind(on_release=self.select_probe)
        layout.add_widget(select_btn)

        back_btn = Button(text="Zurück", size_hint_y=None, height=40)
        back_btn.bind(on_release=self.go_back)
        layout.add_widget(back_btn)

        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self.load_proben(), 0.1)

        self.selected_probe = None

    def load_proben(self):
        """Lädt alle Proben in eine Scrollliste."""
        try:
            load_dotenv()
            base_url = os.getenv("BASEROW_URL")
            api_token = os.getenv("API_TOKEN")

            if not base_url or not api_token:
                self.status_label.text = "Fehlende URL oder Token"
                return

            headers = {"Authorization": f"Token {api_token}"}
            api_url = f"{base_url}database/rows/table/749/?user_field_names=true"
            r = requests.get(api_url, headers=headers, timeout=10)

            if r.status_code != 200:
                self.status_label.text = f"Fehler: {r.status_code}"
                print("[ERROR] load_proben:", r.text)
                return

            data = r.json().get("results", [])
            data.sort(key=lambda x: x.get("Datum", ""), reverse=True)

            self.grid.clear_widgets()
            for probe in data:
                pid = probe.get("id")
                name = probe.get("Name", "Unbenannt")
                datum = probe.get("Datum", "unbekannt")
                btn = Button(text=f"{datum} – {name}", size_hint_y=None, height=44)
                btn.bind(on_release=lambda inst, pid=pid: self.select_in_list(pid, inst))
                self.grid.add_widget(btn)

            self.status_label.text = f"{len(data)} Proben geladen"

        except Exception as e:
            self.status_label.text = f"Fehler: {e}"
            print("load_proben ERROR:", e)

    def select_in_list(self, probe_id, instance):
        self.selected_probe = probe_id
        self.status_label.text = f"Ausgewählt: {instance.text}"

    def select_probe(self, instance):
        if not self.selected_probe:
            self.status_label.text = "Bitte zuerst eine Probe auswählen"
            return

        # Screen hinzufügen falls noch nicht vorhanden
        if "edit_selected_probe" not in self.manager.screen_names:
            self.manager.add_widget(EditSelectedProbeScreen(name="edit_selected_probe"))

        # Übergabe der ausgewählten Probe-ID
        target = self.manager.get_screen("edit_selected_probe")
        target.load_probe(self.selected_probe)

        self.manager.current = "edit_selected_probe"

    def go_back(self, instance):
        self.manager.current = "main_menu"




# -----------------------
# PieceSelectorAddOnly
# -----------------------
class PieceSelectorAddOnly(BoxLayout):
    def __init__(self, all_pieces, selected_set=None, **kwargs):
        super().__init__(orientation="vertical", spacing=5, size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter("height"))
        self.all_pieces = all_pieces or []
        self.selected_set = selected_set or set()
        self.on_add_callback = None  # Wird aufgerufen, wenn ein Stück hinzugefügt wurde

        # Überschrift + Eingabe
        self.add_widget(Label(text="Neues Stück hinzufügen:", size_hint_y=None, height=25))
        self.input_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=35, spacing=5)
        self.text_input = TextInput(hint_text="Stückname eingeben...", multiline=False)
        self.btn_add = Button(text="Stück hinzufügen", size_hint_x=None, width=150)
        self.btn_add.bind(on_release=self._on_add_piece)
        self.input_box.add_widget(self.text_input)
        self.input_box.add_widget(self.btn_add)
        self.add_widget(self.input_box)

        # Vorschlagsbox für Autovervollständigung
        self.suggestion_box = BoxLayout(orientation="vertical", spacing=3, size_hint_y=None)
        self.suggestion_box.bind(minimum_height=self.suggestion_box.setter("height"))
        self.text_input.bind(text=self.on_text)
        self.add_widget(self.suggestion_box)

        # Label für bereits hinzugefügte Stücke
        self.add_widget(Label(text="Bereits hinzugefügte Stücke:", size_hint_y=None, height=25))

        # Anzeige bereits ausgewählter Stücke (wächst automatisch)
        self.selected_box = BoxLayout(orientation="vertical", spacing=3, size_hint_y=None)
        self.selected_box.bind(minimum_height=self.selected_box.setter("height"))
        self.add_widget(self.selected_box)

        # Initial füllen
        self._refresh_selected_display()

    # --------------------------------------------
    def _format_piece_text(self, piece):
        """Formatiert Stückname - Heft/Noten - S. #"""
        parts = [piece.get("value", "Unbenannt")]
        heft = piece.get("Heft/Noten")
        seite = piece.get("Seite")
        if heft:
            parts.append(str(heft))
        if seite:
            parts.append(f"S. {seite}")
        return " - ".join(parts)

    # --------------------------------------------
    def on_text(self, instance, value):
        """Zeigt Vorschläge basierend auf der Eingabe."""
        self.suggestion_box.clear_widgets()
        query = value.strip().lower()
        if not query:
            return
        matches = [p for p in self.all_pieces if query in p["value"].lower()]
        print(f"[DEBUG] found {len(matches)} matching pieces for '{value}'")

        for p in matches[:10]:
            btn = Button(
                text=self._format_piece_text(p),
                size_hint_y=None,
                height=30,
                halign="left",
                valign="middle"
            )
            btn.bind(on_release=lambda b, pid=p["id"]: self._add_piece_by_id(pid))
            self.suggestion_box.add_widget(btn)

    # --------------------------------------------
    def _add_piece_by_id(self, pid):
        """Wird aufgerufen, wenn ein Vorschlag ausgewählt wird."""
        self.selected_set.add(pid)
        self.text_input.text = ""
        self.suggestion_box.clear_widgets()
        self._refresh_selected_display()
        if callable(self.on_add_callback):
            self.on_add_callback()

    # --------------------------------------------
    def _on_add_piece(self, instance):
        """Manuelles Hinzufügen per Button."""
        name = self.text_input.text.strip()
        if not name:
            return
        existing = next((p for p in self.all_pieces if p["value"].strip().lower() == name.lower()), None)
        if existing:
            pid = existing["id"]
        else:
            pid = max([p["id"] for p in self.all_pieces], default=0) + 1
            self.all_pieces.append({"id": pid, "value": name})
        self.selected_set.add(pid)
        self.text_input.text = ""
        self.suggestion_box.clear_widgets()
        self._refresh_selected_display()
        if callable(self.on_add_callback):
            self.on_add_callback()

    # --------------------------------------------
    def _refresh_selected_display(self):
        """Zeigt die bereits ausgewählten Stücke an."""
        self.selected_box.clear_widgets()
        selected_pieces = [p for p in self.all_pieces if p["id"] in self.selected_set]
        if not selected_pieces:
            self.selected_box.add_widget(Label(
                text="(Noch keine Stücke ausgewählt)",
                size_hint_y=None,
                height=25,
                italic=True
            ))
            return
        for p in selected_pieces:
            lbl = Label(
                text=f"• {self._format_piece_text(p)}",
                size_hint_y=None,
                height=25,
                halign='left',
                valign='middle'
            )
            lbl.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
            self.selected_box.add_widget(lbl)



# -----------------------
# EditSelectedProbeScreen (korrigiert)
# -----------------------
class EditSelectedProbeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.probe_id = None
        self.players = []  # wird mit Einträgen {'id','display','_raw'} gefüllt
        self.selected_dabei = set()
        self.selected_entschuldigt = set()
        self.dabei_checkboxes = []
        self.entschuldigt_checkboxes = []

        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=5)
        self.status_label = Label(text="Probe bearbeiten", size_hint_y=None, height=30)
        self.layout.add_widget(self.status_label)

        self.scroll = ScrollView(size_hint=(1, 0.85))
        self.grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)

        save_btn = Button(text="Änderungen speichern", size_hint_y=None, height=40)
        save_btn.bind(on_release=self.save_changes)
        self.layout.add_widget(save_btn)

        back_btn = Button(text="Zurück", size_hint_y=None, height=40)
        back_btn.bind(on_release=self.go_back)
        self.layout.add_widget(back_btn)

        self.add_widget(self.layout)

    # Hilfsfunktion zur Anzeige von Spielernamen
    def _player_display_name(self, player):
        pairs = [("Vorname", "Nachname"), ("vorname", "nachname"),
                 ("first_name", "last_name"), ("firstName", "lastName"),
                 ("given_name", "family_name"), ("FirstName", "LastName")]
        for a, b in pairs:
            if a in player and b in player and player[a] and player[b]:
                return f"{player[a].strip()} {player[b].strip()}"
        for single in ("Name", "name", "FullName", "full_name"):
            if single in player and player[single]:
                return player[single].strip()
        for k, v in player.items():
            if isinstance(v, str) and v.strip():
                return v.strip()
        return f"Spieler {player.get('id')}"

    # load_probe: BEACHTE -> Spieler werden jetzt AUF JEDEN FALL vor den Checkboxes geladen
    def load_probe(self, probe_id):
        self.probe_id = probe_id
        self.grid.clear_widgets()
        self.status_label.text = f"Lade Probe {probe_id} ..."

        load_dotenv()
        base_url = os.getenv("BASEROW_URL")
        api_token = os.getenv("API_TOKEN")
        if not base_url or not api_token:
            self.status_label.text = "Fehlende BASEROW_URL oder API_TOKEN"
            return
        headers = {"Authorization": f"Token {api_token}"}

        try:
            # -------------------------
            # Probe abrufen
            # -------------------------
            r = requests.get(f"{base_url}database/rows/table/749/{probe_id}/?user_field_names=true",
                            headers=headers, timeout=10)
            if r.status_code != 200:
                self.status_label.text = f"Fehler beim Laden der Probe ({r.status_code})"
                print("[ERROR] load_probe GET probe:", r.text)
                return
            probe = r.json()
            print("[DEBUG] raw probe data:", probe)

            # -------------------------
            # Spieler abrufen
            # -------------------------
            r2 = requests.get(f"{base_url}database/rows/table/495/?user_field_names=true",
                            headers=headers, timeout=10)
            if r2.status_code != 200:
                self.status_label.text = f"Fehler beim Laden der Spieler ({r2.status_code})"
                print("[ERROR] load_probe GET players:", r2.text)
                return
            players_raw = r2.json().get("results", [])

            # Spieler aufbereiten
            players = []
            for p in players_raw:
                display = self._player_display_name(p)
                if not re.search(r"[A-Za-zÄÖÜäöüß]", str(display)):
                    continue
                players.append({"id": p.get("id"), "display": display, "_raw": p})
            players.sort(key=lambda x: (x["display"].split()[-1].lower(), x["display"].lower()))
            self.players = players

            # -------------------------
            # Probe Name + Notizen
            # -------------------------
            pname = probe.get("Name") or "Unbenannt"
            self.grid.add_widget(Label(text=f"Probe: {pname}", size_hint_y=None, height=30))

            self.grid.add_widget(Label(text="Notizen:", size_hint_y=None, height=30))
            self.notes_input = TextInput(text=str(probe.get("Notes") or ""), size_hint_y=None, height=100)
            self.grid.add_widget(self.notes_input)
            self.original_notes = str(probe.get("Notes") or "")

            # -------------------------
            # Aufgef. Stücke (Add-only)
            # -------------------------
            self.grid.add_widget(Label(
                text="Aufgef. Stücke:",
                size_hint_y=None,
                height=30,
                font_size=20
            ))

            r3 = requests.get(f"{base_url}database/rows/table/747/?user_field_names=true", headers=headers, timeout=10)
            if r3.status_code == 200:
                all_pieces = [
                    {
                        "id": p["id"],
                        "value": f"{p.get('Name','')} - {p.get('Heft/Noten','')} - S. {p.get('Seite','')}".strip(" -")
                    } for p in r3.json().get("results", [])
                ]
            else:
                all_pieces = []

            pre_pieces = probe.get("aufgef. Stücke", []) or []
            selected_pieces = set(p["id"] for p in pre_pieces if isinstance(p, dict) and "id" in p)

            self.piece_selector = PieceSelectorAddOnly(all_pieces, selected_set=selected_pieces)
            # Callback, damit Anzeige bei Auswahl direkt aktualisiert wird
            self.piece_selector.on_add_callback = lambda: None
            self.grid.add_widget(self.piece_selector)

            # -------------------------
            # Dabei waren (Spieler)
            # -------------------------
            self.grid.add_widget(Label(
                text="Dabei waren:",
                size_hint_y=None,
                height=30,
                font_size=20,
                color=get_color_from_hex("#00AA00")
            ))
            self.dabei_checkboxes = []
            pre_dabei = probe.get("dabei waren", []) or []
            orig_dabei_ids = set(item["id"] for item in pre_dabei if isinstance(item, dict) and "id" in item)
            self.original_dabei = orig_dabei_ids.copy()
            self.selected_dabei = set(orig_dabei_ids)
            self._add_checkboxes_from_players(self.players, self.dabei_checkboxes, pre_dabei, self.selected_dabei)

            # -------------------------
            # Entschuldigt (Spieler)
            # -------------------------
            self.grid.add_widget(Label(
                text="Entschuldigt:",
                size_hint_y=None,
                height=30,
                font_size=20,
                color=get_color_from_hex("#AA0000")
            ))
            self.entschuldigt_checkboxes = []
            pre_ents = probe.get("entschuldigt", []) or []
            orig_ents_ids = set(item["id"] for item in pre_ents if isinstance(item, dict) and "id" in item)
            self.original_entschuldigt = orig_ents_ids.copy()
            self.selected_entschuldigt = set(orig_ents_ids)
            self._add_checkboxes_from_players(self.players, self.entschuldigt_checkboxes, pre_ents, self.selected_entschuldigt)

            self.status_label.text = f"Probe '{pname}' geladen ✅"

        except Exception as e:
            self.status_label.text = f"Fehler: {e}"
            print("load_probe ERROR:", e)






    # Checkbox-Liste bauen
    def _add_checkboxes_from_players(self, players, store_list, preselected, selected_set):
        pre_ids = set(item["id"] for item in preselected if isinstance(item, dict) and "id" in item)
        for pl in players:
            pid, pname = pl["id"], pl["display"]
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
            cb = CheckBox(active=(pid in pre_ids), size_hint_x=0.15)
            lbl = Label(text=pname, size_hint_x=0.85, halign='left', valign='middle')
            lbl.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
            box.add_widget(cb)
            box.add_widget(lbl)
            self.grid.add_widget(box)
            store_list.append((cb, pid))
            if cb.active:
                selected_set.add(pid)
            cb.bind(active=self._make_checkbox_handler(pid, selected_set))

    def _make_checkbox_handler(self, pid, target_set):
        def handler(instance, value):
            if value:
                target_set.add(pid)
            else:
                target_set.discard(pid)
        return handler

    # Anzeige der ausgewählten Stücke (wird vom PieceSelector und initial genutzt)
    def _update_selected_pieces_display(self, pieces):
        self.selected_pieces_box.clear_widgets()
        if not pieces:
            self.selected_pieces_box.add_widget(Label(text="(Noch keine Stücke ausgewählt)",
                                                      size_hint_y=None, height=25, italic=True))
            return
        for p in pieces:
            pname = p.get("value") if isinstance(p, dict) else str(p)
            lbl = Label(text=f"• {pname}", size_hint_y=None, height=25, halign='left', valign='middle')
            lbl.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
            self.selected_pieces_box.add_widget(lbl)

    # Speichern (wie vorher)
    def save_changes(self, instance):
        if not self.probe_id:
            self.status_label.text = "Keine Probe geladen"
            return

        load_dotenv()
        base_url = os.getenv("BASEROW_URL")
        api_token = os.getenv("API_TOKEN")
        if not base_url or not api_token:
            self.status_label.text = "Fehlende BASEROW_URL oder API_TOKEN"
            return
        headers = {"Authorization": f"Token {api_token}"}

        payload = {}
        current_notes = self.notes_input.text or ""
        if current_notes != getattr(self, "original_notes", ""):
            payload["Notes"] = current_notes
        if set(getattr(self, "selected_dabei", set())) != getattr(self, "original_dabei", set()):
            payload["dabei waren"] = list(self.selected_dabei)
        if set(getattr(self, "selected_entschuldigt", set())) != getattr(self, "original_entschuldigt", set()):
            payload["entschuldigt"] = list(self.selected_entschuldigt)
        if getattr(self, "piece_selector", None) and self.piece_selector.selected_set:
            payload["aufgef. Stücke"] = list(self.piece_selector.selected_set)

        if not payload:
            self.status_label.text = "Keine Änderungen zu speichern"
            return

        try:
            r = requests.patch(
                f"{base_url}database/rows/table/749/{self.probe_id}/?user_field_names=true",
                headers=headers,
                json=payload,
                timeout=10
            )
            if r.status_code == 200:
                self.status_label.text = "Änderungen gespeichert ✅"
                self.original_notes = payload.get("Notes", self.original_notes)
                if "dabei waren" in payload:
                    self.original_dabei = set(payload["dabei waren"])
                if "entschuldigt" in payload:
                    self.original_entschuldigt = set(payload["entschuldigt"])
            else:
                self.status_label.text = f"Fehler beim Speichern: {r.status_code}"
                print("[ERROR] save_changes:", r.status_code, r.text)
        except Exception as e:
            self.status_label.text = f"Fehler: {e}"
            print("save_changes ERROR:", e)

    def go_back(self, instance):
        self.manager.current = "edit_probe"



# -----------------------
# AutocompleteTextInput + AddSheetMusicScreen
# -----------------------
class AutocompleteTextInput(BoxLayout):
    """TextInput mit Autovervollständigung aus einer Liste von Optionen"""
    def __init__(self, all_options=None, hint="", **kwargs):
        super().__init__(orientation="vertical", spacing=3, **kwargs)
        self.all_options = all_options or []

        self.text_input = TextInput(hint_text=hint, multiline=False)
        self.add_widget(self.text_input)

        self.suggestion_box = BoxLayout(orientation="vertical", spacing=2, size_hint_y=None)
        self.suggestion_box.bind(minimum_height=self.suggestion_box.setter("height"))
        self.scroll = ScrollView(size_hint=(1, None), height=100)
        self.scroll.add_widget(self.suggestion_box)
        self.add_widget(self.scroll)

        self.text_input.bind(text=self.on_text)

    def on_text(self, instance, value):
        self.suggestion_box.clear_widgets()
        query = value.strip().lower()
        if not query:
            return
        matches = [opt for opt in self.all_options if query in opt.lower()]
        for m in matches[:10]:
            btn = Button(text=m, size_hint_y=None, height=30)
            btn.bind(on_release=lambda b, text=m: self.select(text))
            self.suggestion_box.add_widget(btn)

    def select(self, text):
        self.text_input.text = text
        self.suggestion_box.clear_widgets()

    def get_text(self):
        return self.text_input.text.strip()


class AddSheetMusicScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=5)
        self.add_widget(self.layout)

        self.layout.add_widget(Label(text="Notenstück hinzufügen", font_size=20, size_hint_y=None, height=30))

        # Name
        self.layout.add_widget(Label(text="Name *", size_hint_y=None, height=25))
        self.name_input = TextInput(multiline=False, size_hint_y=None, height=35)
        self.layout.add_widget(self.name_input)

        # Heft/Noten
        self.layout.add_widget(Label(text="Heft/Noten *", size_hint_y=None, height=25))
        self.heft_input = AutocompleteTextInput(hint="Heft/Noten")
        self.layout.add_widget(self.heft_input)

        # Seite (optional)
        self.layout.add_widget(Label(text="Seite (optional)", size_hint_y=None, height=25))
        self.page_input = TextInput(multiline=False, size_hint_y=None, height=35)
        self.layout.add_widget(self.page_input)

        # Komponist (optional)
        self.layout.add_widget(Label(text="Komponist (optional)", size_hint_y=None, height=25))
        self.composer_input = AutocompleteTextInput(hint="Komponist")
        self.layout.add_widget(self.composer_input)

        # Buttons
        btn_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=40, spacing=10)
        save_btn = Button(text="Hinzufügen")
        save_btn.bind(on_release=self.save_sheetmusic)
        cancel_btn = Button(text="Abbrechen")
        cancel_btn.bind(on_release=self.go_back)
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        self.layout.add_widget(btn_layout)

        # Status
        self.status_label = Label(text="", size_hint_y=None, height=30)
        self.layout.add_widget(self.status_label)

        # Optionen für Autocomplete laden
        self.load_existing_options()

    def load_existing_options(self):
        """Lädt vorhandene Heft/Noten und Komponisten aus Tabelle 747"""
        load_dotenv()
        base_url = os.getenv("BASEROW_URL")
        api_token = os.getenv("API_TOKEN")
        if not base_url or not api_token:
            self.status_label.text = "BASEROW_URL oder API_TOKEN fehlt"
            return
        headers = {"Authorization": f"Token {api_token}"}
        try:
            r = requests.get(f"{base_url}database/rows/table/747/?user_field_names=true", headers=headers, timeout=10)
            if r.status_code != 200:
                self.status_label.text = f"Fehler beim Laden: {r.status_code}"
                return
            results = r.json().get("results", [])
            heft_options = list({row.get("Heft/Noten") for row in results if row.get("Heft/Noten")})
            komponist_options = list({row.get("Komponist") for row in results if row.get("Komponist")})
            self.heft_input.all_options = heft_options
            self.composer_input.all_options = komponist_options
        except Exception as e:
            self.status_label.text = f"Lade-Fehler: {e}"

    def save_sheetmusic(self, instance):
        name = self.name_input.text.strip()
        heft = self.heft_input.get_text()
        page = self.page_input.text.strip()
        composer = self.composer_input.get_text()

        if not name or not heft:
            Popup(title="Fehler", content=Label(text="Bitte Name und Heft/Noten ausfüllen"),
                  size_hint=(0.6, 0.4)).open()
            return

        payload = {"Name": name, "Heft/Noten": heft}
        if page:
            payload["Seite"] = page
        if composer:
            payload["Komponist"] = composer

        print("[DEBUG] Payload to send:", payload)

        load_dotenv()
        base_url = os.getenv("BASEROW_URL")
        api_token = os.getenv("API_TOKEN")
        if not base_url or not api_token:
            print("[ERROR] BASEROW_URL or API_TOKEN missing")
            return
        headers = {"Authorization": f"Token {api_token}"}

        try:
            r = requests.post(f"{base_url}database/rows/table/747/?user_field_names=true",
                              headers=headers, json=payload, timeout=10)
            if r.status_code == 200:
                print("[INFO] Notenstück erfolgreich hinzugefügt")
                # Felder leeren
                self.name_input.text = ""
                self.heft_input.text_input.text = ""
                self.page_input.text = ""
                self.composer_input.text_input.text = ""
                # Optionen aktualisieren
                self.load_existing_options()
                self.status_label.text = "Stück hinzugefügt ✅"
            else:
                print("[ERROR] Fehler beim Hinzufügen:", r.status_code, r.text)
                self.status_label.text = f"Fehler: {r.status_code}"
        except Exception as e:
            print("[ERROR] Exception beim Hinzufügen:", e)
            self.status_label.text = f"Fehler: {e}"

    def go_back(self, instance):
        self.manager.current = "main_menu"



# ---------------------------------------------------
# 🔹 App
# ---------------------------------------------------
class BaserowApp(App):
    def build(self):
        print("[DEBUG] Starte build() …")
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainMenu(name="main_menu"))
        sm.add_widget(AddProbeScreen(name="add_probe"))
        sm.add_widget(EditProbeScreen(name="edit_probe"))
        sm.add_widget(EditSelectedProbeScreen(name="edit_selected_probe"))
        sm.add_widget(AddSheetMusicScreen(name="add_sheet_music"))

        sm.current = "login"
        return sm

    def on_start(self):
        print("[INFO] App gestartet – prüfe gespeicherte URL & Login …")

        # Shortlink / BASEROW_URL holen
        verify_or_refresh_baserow_url()

        # Auto-Login verzögert starten, damit ScreenManager & Screens komplett gesetzt sind
        Clock.schedule_once(self.attempt_login, 0.1)

    def attempt_login(self, dt):
        if login_to_baserow():
            print("[OK] Login erfolgreich, Hauptmenü wird angezeigt")
            if self.root:
                self.root.current = "main_menu"
        else:
            print("[WARN] Kein gespeicherter Login möglich – zeige Login-Screen")
            if self.root:
                self.root.current = "login"




if __name__ == "__main__":
    BaserowApp().run()
