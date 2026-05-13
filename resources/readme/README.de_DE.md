<div align="center">

![PalworldSaveTools Logo](../PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Ein umfassendes Toolkit zur Bearbeitung gespeicherter Dateien für Palworld**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

---

### **Laden Sie die Standalone-Version von [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** herunter

---

</div>

## Inhaltsverzeichnis

- [Funktionen](#funktionen)
- [Installation](#installation)
- [Schnellstart](#schnellstart)
- [Tools-Übersicht](#tools-übersicht)
- [Anleitungen](#anleitungen)
- [Fehlerbehebung](#fehlerbehebung)
- [Erstellen einer eigenständigen ausführbaren Datei (nur Windows)](#erstellen-einer-eigenständigen-ausführbaren-datei-nur-windows)
- [Mitwirken](#mitwirken)
- [Lizenz](#lizenz)

---

## Funktionen

### Kernfunktionalität

| Funktion | Beschreibung |
|---------|-------------|
| **Schnelles Speichern-Parsing** | Einer der schnellsten verfügbaren Lesegeräte für gespeicherte Dateien |
| **Spielerverwaltung** | Anzeigen, Bearbeiten, Umbenennen, Level ändern, Technologien freischalten und Spieler verwalten |
| **Gildenverwaltung** | Spieler erstellen, umbenennen, verschieben, Laborforschung freischalten und Gilden verwalten |
| **Pal Editor** | Vollständiger Editor für Statistiken, Fähigkeiten, IVs, Rang, Seelen, Geschlecht, Boss/Glücksschalter |
| **Basislager-Werkzeuge** | Exportieren, importieren, klonen, Radius anpassen und Basen verwalten |
| **Kartenbetrachter** | Interaktive Basis- und Spielerkarte mit Koordinaten und Details |
| **Charakterübertragung** | Charaktere zwischen verschiedenen Welten/Servern übertragen (Cross-Save) |
| **Konvertierung speichern** | Konvertieren zwischen den Formaten Steam und GamePass |
| **Welteinstellungen** | WorldOption- und LevelMeta-Einstellungen bearbeiten |
| **Zeitstempel-Tools** | Negative Zeitstempel korrigieren und Spielerzeiten zurücksetzen |

### All-in-One-Tools

Die Suite **All-in-One Tools** bietet umfassende Speicherverwaltung:

- **Löschtools**
  - Löschen Sie Spieler, Basen oder Gilden
  - Löschen Sie inaktive Spieler basierend auf Zeitschwellen
  - Entfernen Sie doppelte Spieler und leere Gilden
  - Löschen Sie nicht referenzierte/verwaiste Daten

- **Bereinigungstools**
  - Entfernen Sie ungültige/modifizierte Elemente
  - Entfernen Sie ungültige pals und passives
  - Behebung des illegalen pals (Obergrenze für zulässige Höchstwerte)
  - Entfernen Sie ungültige Strukturen
  - Luftabwehrtürme zurücksetzen
  - Schalte private chests frei

- **Gildenwerkzeuge**
  - Alle Gilden neu aufbauen
  - Verschieben Sie Spieler zwischen Gilden
  - Ernenne den Spieler zum Gildenführer
  - Gilden umbenennen
  - Maximales Gildenlevel
  - Schalten Sie alle Laborforschungen frei

- **Player-Tools**
  - Bearbeiten Sie die Statistiken und Fähigkeiten des Spielers pal
  - Schalten Sie alle Technologien frei
  - Schalte den Sichtkäfig frei
  - Spieler im Level auf-/absteigen
  - Spieler umbenennen

- **Dienstprogramme speichern**
  - Missionen zurücksetzen
  - Dungeons zurücksetzen
  - Zeitstempel korrigieren
  - Abbau überfüllter Lagerbestände
  - Generieren Sie PalDefender-Befehle

### Zusätzliche Tools

| Werkzeug | Beschreibung |
|------|-------------|
| **Spieler Pals** bearbeiten | Vollständiger pal editor mit Statistiken, Fähigkeiten, IVs, Talenten, Seelen, Rang und Geschlecht |
| **SteamID-Konverter** | Konvertieren Sie Steam-IDs in Palworld-UIDs |
| **Host-Speicherung beheben** | UIDs zwischen zwei Spielern austauschen (z. B. für Host-Swap) |
| **Schlitzinjektor** | Palbox-Slots pro Spieler erhöhen |
| **Karte wiederherstellen** | Wende den freigeschalteten Kartenfortschritt auf alle Welten/Server an |
| **Welt umbenennen** | Ändern Sie den Weltnamen in LevelMeta |
| **WorldOption-Editor** | Welteinstellungen und Konfiguration bearbeiten |
| **LevelMeta-Editor** | Weltmetadaten bearbeiten (Name, Host, Ebene) |

---

## Installation

### Voraussetzungen

**Für Standalone (Windows):**
- Windows 10/11
- [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version) (2015-2022)

**Zur Ausführung von der Quelle (alle Plattformen):**
- Python 3.11 oder höher

### Eigenständig (Windows – empfohlen)

1. Laden Sie die neueste Version von [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) herunter
2. Extrahieren Sie die ZIP-Datei
3. Führen Sie `PalworldSaveTools.exe` aus

### Aus der Quelle (Alle Plattformen)

Die Startskripte erstellen automatisch eine virtuelle Umgebung und installieren alle Abhängigkeiten.

**Mit uv:**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv venv --python 3.12
uv run start.py
```

**Windows:**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
start_win.cmd
```

**Linux:**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
chmod +x start_linux.sh
./start_linux.sh
```

### Zweige

- **Stabil** (empfohlen): `git clone https://github.com/deafdudecomputers/PalworldSaveTools.git`
- **Beta** (neueste Funktionen): `git clone -b beta https://github.com/deafdudecomputers/PalworldSaveTools.git`

---

## Schnellstart

1. **Laden Sie Ihren Speicherstand**
   - Klicken Sie auf die Menüschaltfläche in der Kopfzeile
   - Wählen Sie **Laden speichern**
   - Navigieren Sie zu Ihrem Palworld-Speicherordner
   - Wählen Sie `Level.sav`

2. **Erkunden Sie Ihre Daten**
   - Verwenden Sie die Registerkarten, um Spieler, Gilden, Stützpunkte oder die Karte anzuzeigen
   - Suchen und filtern Sie, um bestimmte Einträge zu finden

3. **Änderungen vornehmen**
   - Wählen Sie Elemente zum Bearbeiten, Löschen oder Ändern aus
   - Klicken Sie mit der rechten Maustaste, um Kontextmenüs mit zusätzlichen Optionen anzuzeigen

4. **Speichern Sie Ihre Änderungen**
   - Klicken Sie auf die Menüschaltfläche → **Änderungen speichern**
   - Backups werden automatisch erstellt

---

## Tools-Übersicht

### All-in-One-Tools (AIO)

Die Hauptoberfläche für eine umfassende Speicherverwaltung mit fünf Registerkarten:

**Registerkarte „Spielerinventar“** – Hier können Sie die Inventare aller Spieler auf dem Server anzeigen und verwalten
- Bearbeiten Sie Spielerstatistiken, Inventar und ausgerüstete Ausrüstung.
- Möglichkeit, die Qualität zu bearbeiten, alles aus dem Inventar und der ausgerüsteten Ausrüstung hinzuzufügen oder daraus zu entfernen.

**Registerkarte „Basisinventar“** – Hier können Sie die Inventare aller Basen auf dem Server anzeigen und verwalten.
- Basisinventar bearbeiten.
- Möglichkeit, Container zu leeren, die Qualität zu bearbeiten und alles aus den Basisbeständen hinzuzufügen oder daraus zu entfernen.
- Filterung für etwaige Betrugsmöglichkeiten enthalten.

**Registerkarte „Spieler“** – Alle Spieler auf dem Server anzeigen und verwalten
- Bearbeiten Sie Spielernamen, Level und pal-Zählungen
- Löschen Sie inaktive Spieler
- Spielergilden und letzte Onlinezeit anzeigen

**Registerkarte „Gilden“** – Gilden und ihre Basen verwalten
- Gilden umbenennen, Anführer wechseln
- Basisstandorte und -ebenen anzeigen
- Löschen Sie leere oder inaktive Gilden

**Registerkarte „Stützpunkte“** – Alle Basislager anzeigen
- Basispläne exportieren/importieren
- Klonen Sie Basen für andere Gilden
- Basisradius anpassen

### Kartenbetrachter

Interaktive Visualisierung Ihrer Welt:
- Alle Basisstandorte und Spielerpositionen anzeigen
- Filtern Sie nach Gilde oder Spielername
- Klicken Sie auf die Markierungen, um detaillierte Informationen zu erhalten
- Generieren Sie `killnearestbase`-Befehle für PalDefender

### Charakterübertragung

Charaktere zwischen verschiedenen Welten/Servern übertragen (Cross-Save):
- Transfer einzelner oder aller Spieler
- Bewahrt Charaktere, pals, Inventar und Technologie
– Nützlich für die Migration zwischen Koop- und dedizierten Servern

### Host-Speicherung beheben

UIDs zwischen zwei Spielern tauschen:
- Übertragen Sie den Fortschritt von einem Spieler auf einen anderen
- Unverzichtbar für Host-/Koop-zu-Server-Übertragungen
– Nützlich für den Austausch der Host-Rolle zwischen Spielern
- Nützlich für Plattformwechsel (Xbox ↔ Steam)
– Behebt Probleme bei der Host/Server-UID-Zuweisung
- **Hinweis:** Der betroffene Spieler muss zuerst einen Charakter auf dem Zielspeicher erstellt haben

---

## Anleitungen

### Dateispeicherorte speichern

**Gastgeber/Kooperative:**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Dedizierter Server:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Kartenfreischaltung

<details>
<summary>Klicken Sie hier, um die Anweisungen zum Entsperren der Karte zu erweitern</summary>

1. Kopieren Sie `LocalData.sav` von `resources\`
2. Suchen Sie Ihren Server-/Weltspeicherordner
3. Ersetzen Sie die vorhandene Datei `LocalData.sav` durch die kopierte Datei
4. Starten Sie das Spiel mit einer vollständig freigeschalteten Karte

> **Hinweis:** Verwenden Sie das Tool **Karte wiederherstellen** auf der Registerkarte „Extras“, um die freigeschaltete Karte mit automatischen Backups auf ALLE Ihre Welten/Server gleichzeitig anzuwenden.

</details>

### Host → Serverübertragung

<details>
<summary>Klicken Sie hier, um die Host-zu-Server-Übertragungsanleitung zu erweitern</summary>

1. Kopieren Sie die Ordner `Level.sav` und `Players` vom Hostspeicher
2. In den Speicherordner des dedizierten Servers einfügen
3. Server starten, neuen Charakter erstellen
4. Warten Sie auf die automatische Speicherung und schließen Sie dann
5. Verwenden Sie **Fix Host Save**, um GUIDs zu migrieren
6. Dateien zurückkopieren und starten

**Fix Host Save verwenden:**
- Wählen Sie `Level.sav` aus Ihrem temporären Ordner aus
- Wähle den **alten Charakter** (aus dem Originalspeicher)
- Wähle den **neuen Charakter** (den du gerade erstellt hast)
- Klicken Sie auf **Migrieren**

</details>

### Host Swap (Host wechseln)

<details>
<summary>Klicken Sie hier, um den Host-Swap-Leitfaden zu erweitern</summary>

**Hintergrund:**
– Der Host verwendet immer `0001.sav` – dieselbe UID für jeden Host
- Jeder Client verwendet eine eindeutige reguläre UID-Speicherung (z. B. `123xxx.sav`, `987xxx.sav`)

**Voraussetzungen:**
Für beide Spieler (alter Host und neuer Host) müssen ihre regulären Spielstände generiert werden. Dies geschieht, indem man sich der Welt des Gastgebers anschließt und einen neuen Charakter erstellt.

**Schritte:**

1. **Stellen Sie sicher, dass regelmäßige Speicherungen vorhanden sind**
   - Spieler A (alter Host) sollte einen regulären Speicherstand haben (z. B. `123xxx.sav`)
   - Spieler B (neuer Host) sollte einen regulären Speicherstand haben (z. B. `987xxx.sav`)

2. **Host-Speicherung des alten Hosts gegen reguläre Speicherung austauschen**
   - Verwenden Sie PalworldSaveTools **Fix Host Save**, um Folgendes auszutauschen:
   - `0001.sav` → `123xxx.sav` des alten Gastgebers
   - (Dies verschiebt den Fortschritt des alten Hosts vom Host-Slot auf seinen regulären Spielerslot)

3. **Tauschen Sie den regulären Speicher des neuen Hosts gegen den Host-Speicher aus**
   - Verwenden Sie PalworldSaveTools **Fix Host Save**, um Folgendes auszutauschen:
   - `987xxx.sav` → `0001.sav` des neuen Hosts
   - (Dies verschiebt den Fortschritt des neuen Hosts in den Host-Slot)

**Ergebnis:**
- Spieler B ist jetzt der Gastgeber mit seinem eigenen Charakter und pals in `0001.sav`
- Spieler A wird mit seinem ursprünglichen Fortschritt in `123xxx.sav` Kunde.

</details>

### Basis-Export/Import

<details>
<summary>Klicken Sie hier, um die Basis-Export-/Importanleitung zu erweitern</summary>

**Eine Basis exportieren:**
1. Laden Sie Ihren Speicherstand im PST-Format
2. Gehen Sie zur Registerkarte „Basen“.
3. Klicken Sie mit der rechten Maustaste auf eine Basis → Basis exportieren
4. Als `.json`-Datei speichern

**Eine Basis importieren:**
1. Gehen Sie zur Registerkarte „Basen“ oder zum Base Map Viewer
2. Klicken Sie mit der rechten Maustaste auf die Gilde, in die Sie die Basis importieren möchten
3. Wählen Sie Basis importieren
4. Wählen Sie Ihre exportierte `.json`-Datei aus

**Klonen einer Basis:**
1. Klicken Sie mit der rechten Maustaste auf eine Basis → Basis klonen
2. Zielgilde auswählen
3. Die Basis wird mit versetzter Positionierung geklont

**Anpassen des Basisradius:**
1. Klicken Sie mit der rechten Maustaste auf eine Basis → Radius anpassen
2. Neuen Radius eingeben (50 % - 1000 %)
3. Speichern und laden Sie den Speicherstand im Spiel, damit Strukturen neu zugewiesen werden können

</details>

---

## Fehlerbehebung

### „VCRUNTIME140.dll wurde nicht gefunden“

**Lösung:** Installieren Sie [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version)

### `struct.error` beim Parsen und Speichern

**Ursache:** Veraltetes Speicherdateiformat

**Lösung:**
1. Laden Sie den Speicherstand im Spiel (Solo-, Coop- oder Dedicated-Server-Modus).
2. Dadurch wird eine automatische Strukturaktualisierung ausgelöst
3. Stellen Sie sicher, dass der Speicherstand mit oder nach dem neuesten Spiel-Patch aktualisiert wurde

### GamePass Konverter funktioniert nicht

**Lösung:**
1. Schließen Sie die GamePass-Version von Palworld
2. Warten Sie einige Minuten
3. Führen Sie den Konverter Steam → GamePass aus
4. Starten Sie Palworld zur Überprüfung auf GamePass

---

## Erstellen einer eigenständigen ausführbaren Datei (nur Windows)

Führen Sie das Build-Skript aus, um eine eigenständige ausführbare Datei zu erstellen:

```bash
scripts\build.cmd
```

Dadurch wird `PST_standalone_v{version}.7z` im Projektstamm erstellt.

---

## Mitwirken

Beiträge sind willkommen! Bitte senden Sie gerne einen Pull Request.

1. Forken Sie das Repository
2. Erstellen Sie Ihren Feature-Zweig (`git checkout -b feature/AmazingFeature`)
3. Übernehmen Sie Ihre Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zur Verzweigung (`git push origin feature/AmazingFeature`)
5. Öffnen Sie eine Pull-Anfrage

---

## Haftungsausschluss

**Die Verwendung dieses Tools erfolgt auf eigene Gefahr. Sichern Sie immer Ihre Sicherungsdateien, bevor Sie Änderungen vornehmen.**

Die Entwickler sind nicht verantwortlich für den Verlust gespeicherter Daten oder Probleme, die durch die Verwendung dieses Tools entstehen können.

---

## Unterstützung

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub Probleme:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Dokumentation:** [Wiki](https://github.com/deafdudecomputers/PalworldSaveTools/wiki) *(Derzeit in Entwicklung)*

---

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert – Einzelheiten finden Sie in der Datei [LICENSE](LICENSE).

---

## Danksagungen

- **Palworld** entwickelt von Pocketpair, Inc.
- Vielen Dank an alle Mitwirkenden und Community-Mitglieder, die zur Verbesserung dieses Tools beigetragen haben

---

<div align="center">

**Hergestellt mit ❤️ für die Palworld-Community**

[⬆ Back to Top](#palworldsavetools)

</div>