<div align="center">

![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)

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
<div align="center">

## Übersicht

<img src="https://readme-typing-svg.demolab.com?lines=Was+genau+ist+dieses+Ding%3F;Ihr+Speicher%2C+Ihr+Weg;Ein+Werkzeug%2C+um+sie+alle+zu+beherrschen&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) ist eine schnelle All-in-One-Desktopanwendung zum Überprüfen und Bearbeiten von Palworld-Sicherungsdateien. Es wurde mit Python und PySide6 erstellt und liest und schreibt das komprimierte Speicherformat des Spiels direkt – keine Spielmodifikationen erforderlich.

Ganz gleich, ob Sie einen dedizierten Server verwalten, zwischen kooperativen und dedizierten Servern migrieren, aufgegebene Daten bereinigen oder einzelne Pals optimieren müssen, PST bietet für alles eine einzige einheitliche Schnittstelle.

### Highlights

- **Plattformübergreifend** – Vorgefertigte Binärdateien für **Windows**, **Linux** und **macOS**.
- **Schnelles natives Parsen** – Einer der schnellsten verfügbaren Lesegeräte für gespeicherte Dateien, angetrieben von der [`palsav`](src/palsav)-Engine.
- **Visuelle Karte** – Interaktive Weltkarte mit Basis-/Spielermarkierungen, Sperrzonen und Koordinatenkalibrierung.
- **Umfassende Pal-Bearbeitung** – Volle Kontrolle über Statistiken, IVs, Seelen, Fertigkeiten, passives, Arbeitseignungen, Rang und Aussehensmarkierungen.
- **Tools auf Serverniveau** – Massenlöschung, Bereinigung, Konvertierung und Zeichenübertragung für Administratoren.
- **Automatische Backups** – Bei jedem Speichervorgang wird vor dem Schreiben ein Backup erstellt.
- **8 Sprachen** – Lokalisierte Benutzeroberfläche, In-App-Anleitungen und Dokumentation.





---





## Inhaltsverzeichnis

- [Übersicht](#übersicht)
- [Funktionen](#funktionen)
- [Installation](#installation)
- [Schnellstart](#schnellstart)
- [Anleitungen](#anleitungen)
- [Fehlerbehebung](#fehlerbehebung)
- [Aufbau aus der Quelle](#aufbau-aus-der-quelle)
- [Mitwirken](#mitwirken)
- [Lizenz](#lizenz)
- [Das Palworld-Team](#das-palworld-team)

- [Unterstützung](#support)
- [Lizenz](#license)
- [Danksagungen](#acknowledgments)





---




<div align="center">

## Funktionen

<img src="https://readme-typing-svg.demolab.com?lines=Das+gute+Zeug;Probieren+Sie+es+aus;Vollgepackt+mit+Werkzeugen&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Spielerverwaltung

- Alle Spieler nach Name, Level, pal-Anzahl, UID, Gilde und zuletzt gesehener Zeit anzeigen und durchsuchen.
- Bearbeiten Sie Spielernamen, Level, Statistiken und Technologiepunkte.
- **Massenoperationen** für mehrere Spieler: Gegenstandsverwaltung, pal-Verwaltung und Technologie-Freischaltungen.
- Inaktive Spieler nach Zeitschwelle löschen; Duplikate entfernen.

### Pal Editor

Eine umfassende Bearbeitungsoberfläche für jedes Pal, das einem beliebigen Spieler gehört. Pals werden von **Party** (aktive Truppe) und **Palbox** (Lagerung) organisiert.

- **Statistiken & IVs** – HP, Angriff, Verteidigung (IV 0–100), Level (1–80), Vertrauensrang (0–10).
- **Seelen** – HP, Angriff, Verteidigung, Handwerksgeschwindigkeit (0–20).
- **Fertigkeiten** – Aktive Fertigkeitsauswahl; lerne alle Bewegungen; Fähigkeiten zur Massensynchronisierung in Pals.
- **Passive Eigenschaften** – Passiver Picker mit vollständigen Spieldaten.
- **Arbeitseignung** – Legen Sie individuelle Arbeitseignungsstufen fest (0–10).
- **Aussehensflaggen** – Boss/Alpha, Glück/Glänzend, Erwacht und Importiert/DNA umschalten.
- **Rang & Sperre** – Rang und bevorzugte Sperrstufe festlegen (0–3).
- Neuen Pals hinzufügen oder per Doppelklick schnell löschen.

### Gildenverwaltung

Zweiteilige Ansicht: Gildenliste oben, Mitgliederliste unten.

- Gilden umbenennen, Anführer wechseln, Gildenstufe festlegen, maximale Gildenstufe festlegen.
- Schalten Sie alle Laborforschungen frei; Alle Gilden neu aufbauen.
- Spieler zwischen Gilden verschieben; Leere oder inaktive Gilden löschen.

### Basislager-Werkzeuge

- Alle Basislager mit Gildenzugehörigkeit anzeigen.
- Basis-Blaupausen **Exportieren** nach `.json`; **Importieren** (einzelne oder mehrere Dateien) in jede Gilde.
- **Klonen** Basen für andere Gilden mit versetzter Positionierung.
- **Basisradius anpassen** (50 %–1000 %).
- Löschen Sie inaktive Basen und Nicht-Basiskartenobjekte.

### Kartenbetrachter

Interaktive Visualisierung Ihrer gesamten Welt.

- Basismarker (Haussymbol) und Spielermarker (Personensymbol) mit Detailfeldern.
- Überlagerungen umschalten: Basen, Spieler, Radiusringe, Sperrzonen.
- **Zonenzeichnung** – Zeichnen Sie rechteckige oder polygonale Sperrzonen direkt auf der Karte.
- **Kalibrierungsmodus** – Richten Sie die Karte genau an den Spielkoordinaten aus.
- Weltkarten- und Baumkartenansichten; Filtern Sie nach Gilde oder Spielername.
- Zoomen (1,0x–30,0x), Schwenken, Doppelklick, um zu einer Markierung zu fliegen.
- Rechtsklick-Markierungen und leerer Bereich für Verwaltungsaktionen.

### Bestandsverwaltung

**Spielerinventar** – Drei Unterregisterkarten:
- *Inventar* – Alle Gegenstände und Ausrüstung in der Haupttasche; Menge bearbeiten, hinzufügen, entfernen.
- *Schlüsselgegenstände* – Questgegenstände, Bildnisse und Technologie; Fügen Sie alle Bildnisse/Schlüsselelemente in großen Mengen hinzu.
- *Statistiken* – Level, HP, Ausdauer, Angriff, Verteidigung, Arbeitsgeschwindigkeit, Gewicht.
- Ausrüstungstafel für Waffen, Zubehör, Nahrung, Rüstung, Schild, Gleiter und Modulplätze.
- Schalten Sie alle Karten- und Schnellreisepunkte mit einem Klick frei.

**Basisinventar** – Durchsuchen und verwalten Sie Artikel und arbeiten Sie Pals über alle Basen hinweg:
- Elemente in Containern anzeigen/bearbeiten; durchsichtige Behälter; Containerplätze ändern.
- Gildenübergreifende Gegenstandsoperationen (Gegenstände in allen Gilden finden/entfernen).
- Gildenübergreifende Strukturlöschung.
- Unterregisterkarte **Basis Pals** – Verwalten Sie die jeder Basis zugewiesenen Arbeits-Pals mit vollständigen pal-Editor-Kontextmenüs.

### Ausschlüsse

Schutzlisten, die Spieler, Gilden und Stützpunkte vor Aufräumarbeiten schützen.

- Drei nebeneinander liegende Felder: ausgeschlossene Spieler-UIDs, Gilden-IDs und Basis-IDs.
- Fügen Sie Einträge über Rechtsklick-Kontextmenüs in den Registerkarten „Spieler“, „Gilden“ oder „Basen“ hinzu.
- Ausschlusslisten dauerhaft speichern und laden.
- Erstellen Sie Ihre Liste **bevor** Sie die Massenbereinigung durchführen.

### Werkzeuge speichern

Über die Registerkarte **Tools** als anklickbare Karten zugänglich:

| Werkzeug | Beschreibung |
|------|-------------|
| **Gespeicherte Dateien konvertieren** | Konvertieren zwischen SAV- und JSON-Format |
| **Konvertieren Sie GamePass → Steam** | Konvertieren Sie Xbox/GamePass-Speicherungen in das Steam-Format |
| **Konvertieren SteamID** | Konvertieren Sie Steam-IDs in Palworld-UIDs |
| **Karte wiederherstellen** | Vollständig freigeschalteten Kartenfortschritt auf alle Welten/Server anwenden |
| **Schlitzinjektor** | Palbox-Slots pro Spieler erhöhen |
| **Ändern Speichern** | Rohspeicherdaten öffnen und ändern |
| **Charakterübertragung** | Charaktere zwischen verschiedenen Welten/Servern übertragen (Cross-Save) |
| **Host-Speicherung beheben** | UIDs zwischen zwei Spielern austauschen (Host-Swap, Plattformmigration) |

### Bereinigungs- und Hilfsfunktionen

Diese Server-Vorgänge sind über **Menü → Funktionen** zugänglich und umfassen:

- **Löschen** – Leere Gilden, inaktive Basen/Spieler, doppelte Spieler, nicht referenzierte Daten löschen.
- **Bereinigung** – Ungültige/modifizierte Elemente, ungültige pals und passives, ungültige Strukturen entfernen; unzulässiges pals beheben (Grenze auf zulässiges Maximum); Luftabwehrtürme zurücksetzen; entsperren private chests; alle Strukturen reparieren.
- **Zurücksetzen** – Missionen, Dungeons, Bohrinsel, Eindringling, Versorgungslieferungen zurücksetzen.
- **Zeitstempel** – Negative Zeitstempel korrigieren; Spielerzeiten zurücksetzen.
- **PalDefender** – `killnearestbase`-Befehle generieren.





---




<div align="center">

## Installation

<img src="https://readme-typing-svg.demolab.com?lines=Bringen+Sie+es+in+wenigen+Minuten+zum+Laufen;Herunterladen+und+loslegen;Keine+Einrichtung+erforderlich&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Eigenständige Builds (empfohlen)

Vorgefertigte Binärdateien sind für alle drei Hauptplattformen ab [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) verfügbar:

| Plattform | Herunterladen | Anforderungen |
|----------|----------|--------------|
| **Windows** | `PalworldSaveTools-*.exe` | Windows 10/11, [VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022) |
| **Linux** | `PalworldSaveTools-*-linux` | Jede moderne Distribution |
| **macOS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+ (Monterey oder höher) |

Auch verfügbar auf [Nexus Mods](https://www.nexusmods.com/palworld/mods/3190).

1. Laden Sie den passenden Build für Ihre Plattform herunter.
2. Extrahieren Sie die ausführbare Datei (falls archiviert) und führen Sie sie aus.
3. Das war's – kein Python oder Abhängigkeiten erforderlich.

> **Windows:** Wenn die Meldung „VCRUNTIME140.dll wurde nicht gefunden“ angezeigt wird, installieren Sie [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170).

> **Linux:** Möglicherweise müssen Sie die Datei als ausführbar markieren: `chmod +x PalworldSaveTools-*-linux`

> **macOS:** Wenn Gatekeeper die App blockiert, klicken Sie beim ersten Mal mit der rechten Maustaste → **Öffnen** oder führen Sie `xattr -d com.apple.quarantine /path/to/app` aus.

### Aus der Quelle (Alle Plattformen)

PST verwendet [`uv`](https://docs.astral.sh/uv/) für die Abhängigkeitsverwaltung. Das Startskript erstellt automatisch eine virtuelle Umgebung und installiert alles.

**Voraussetzungen:** [Python 3.11+](https://www.python.org/) und [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows** (Doppelklick-Launcher):
```
start.cmd
```

Der Launcher erstellt einen `.venv`, installiert Abhängigkeiten über `uv sync` und startet die App. Es bereinigt die Sperrdatei beim Beenden, sodass jeder Lauf reproduzierbar ist.





---




<div align="center">

## Schnellstart

<img src="https://readme-typing-svg.demolab.com?lines=Laden.+Bearbeiten.+Speichern.+Das+einfach.;Drei+Schritte+zum+Ruhm;Es+ist+so+einfach&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **Laden Sie Ihren Speicherstand**
   - Klicken Sie auf **Menü → Laden und Speichern** oder ziehen Sie eine `.sav`-Datei per Drag-and-Drop in das Fenster.
   - Navigieren Sie zu Ihrem Palworld-Speicherordner und wählen Sie `Level.sav`.

2. **Erkunden Sie Ihre Daten**
   - Verwenden Sie die Registerkarten – **Karte**, **Tools**, **Spieler**, **Gilden**, **Basen**, **Spielerinventar**, **Basisinventar**, **Pal Editor**, **Ausschlüsse** – um Ihren Speicherstand zu erkunden.
   - Die Statistikleiste zeigt Live-Zählungen; Schnellnavigationssymbole springen zu den einzelnen Abschnitten.

3. **Änderungen vornehmen**
   - Zum Auswählen mit der linken Maustaste klicken; Klicken Sie mit der rechten Maustaste auf fast alles, um kontextbezogene Aktionen auszuführen.
   - Doppelklicken Sie, um schnell zu bearbeiten oder schnell zu löschen (weitere Informationen finden Sie in den In-App-Anleitungen).

4. **Speichern Sie Ihre Änderungen**
   - Klicken Sie auf **Menü → Änderungen speichern**. Backups werden automatisch erstellt.

> **Tipp:** Jede Registerkarte verfügt über eine integrierte Anleitung – klicken Sie in einer beliebigen Registerkarte auf das Hilfesymbol, um genau zu sehen, was sie tun kann. Um tiefere Informationen zu erhalten, **bewegen Sie den Mauszeiger über eine beliebige Schaltfläche, ein Feld oder ein Steuerelement**, um detaillierte Tooltips in der Kopfzeile anzuzeigen. Das In-App-Tooltip-Hilfesystem ist Ihre beste Referenz, um genau zu verstehen, was die einzelnen Funktionen bewirken und wie sie verwendet werden.





---




<div align="center">

## Anleitungen

<img src="https://readme-typing-svg.demolab.com?lines=Schritt-f%C3%BCr-Schritt-Anleitungen;Folgen+Sie+der+Anleitung;Wir+zeigen+Ihnen%2C+wie&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Dateispeicherorte speichern

**Host / Koop (Windows):**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Dedizierter Server:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Kartenfreischaltung

PST kann die vollständige Karte (alle Schnellreisepunkte) für Ihren Speicherstand freischalten:

1. Laden Sie Ihren Speicherstand im PST-Format.
2. Öffnen Sie die Registerkarte **Spielerinventar** und klicken Sie auf **Alle Karten + Schnellreisen freischalten** für einen einzelnen Spieler, **oder**
3. Verwenden Sie das Tool **Karte wiederherstellen** auf der Registerkarte „Extras“, um den freigeschalteten Kartenfortschritt auf **allen** Ihren Welten/Servern gleichzeitig anzuwenden.
4. Änderungen speichern. Es werden automatische Backups erstellt.

### Host → Serverübertragung

<details>
<summary>Zum Erweitern klicken</summary>

1. Kopieren Sie `Level.sav` und den Ordner `Players` von Ihrem Hostspeicher.
2. Fügen Sie sie in den Speicherordner des dedizierten Servers ein.
3. Starten Sie den Server, erstellen Sie einen neuen Charakter und warten Sie auf die automatische Speicherung.
4. Schließen Sie den Server.
5. Verwenden Sie **Fix Host Save** in PST, um die GUID des alten Charakters auf die neue zu migrieren.
6. Kopieren Sie die Dateien zurück und starten Sie den Server.

</details>

### Host Swap (Host wechseln)

<details>
<summary>Zum Erweitern klicken</summary>

**Hintergrund:** Der Host verwendet immer den `0001.sav`-Slot – dieselbe UID für jeden Host. Jeder Client erhält eine eindeutige reguläre Speicherung (z. B. `123xxx.sav`).

**Voraussetzung:** Sowohl der alte als auch der neue Host müssen über einen regulären Speicherstand verfügen, der durch den Beitritt und die Erstellung eines Charakters generiert wird.

**Schritte:**

1. Verwenden Sie **Fix Host Save**, um den `0001.sav` des alten Hosts → seinen regulären Speicher (z. B. `123xxx.sav`) auszutauschen. Dadurch wird ihr Fortschritt aus dem Host-Slot verschoben.
2. Verwenden Sie **Fix Host Save**, um die reguläre Speicherung des neuen Hosts (z. B. `987xxx.sav`) → `0001.sav` auszutauschen. Dadurch wird ihr Fortschritt in den Host-Slot verschoben.

**Ergebnis:** Der neue Host belegt nun `0001.sav` mit seinem eigenen Charakter und Pals; Der alte Host wird zum Client, wobei sein ursprünglicher Fortschritt erhalten bleibt.

</details>

### Charakterübertragung (Cross-Save)

<details>
<summary>Zum Erweitern klicken</summary>

Übertragen Sie Charaktere zwischen verschiedenen Welten oder Servern und bewahren Sie dabei Charaktere, Pals, Inventar und Technologie:

1. Öffnen Sie das Tool **Charakterübertragung** auf der Registerkarte Extras.
2. Wählen Sie den Quellspeicher und den Zielspeicher aus.
3. Transferieren Sie einen einzelnen Spieler oder alle Spieler.
4. Nützlich für die Migration zwischen Koop- und dedizierten Servern.

</details>

### Basisexport / Import / Klonen

<details>
<summary>Zum Erweitern klicken</summary>

**Eine Basis exportieren:**
1. Gehen Sie zur Registerkarte **Stützpunkte** (oder verwenden Sie den Map Viewer).
2. Klicken Sie mit der rechten Maustaste auf eine Basis → **Basis exportieren**.
3. Als `.json`-Blueprint-Datei speichern.

**Eine Basis importieren:**
1. Klicken Sie mit der rechten Maustaste auf die Zielgilde (in der Registerkarte „Basen“, „Map Viewer“ oder „Gilden“).
2. Wählen Sie **Basis importieren** (einzelne Datei) oder **Basen importieren (mehrere Dateien)**.
3. Wählen Sie Ihre exportierte(n) `.json`-Datei(en) aus.

**Klonen einer Basis:**
1. Klicken Sie mit der rechten Maustaste auf eine Basis → **Basis klonen**.
2. Wählen Sie die Zielgilde aus.
3. Die Basis wird mit versetzter Positionierung geklont.

**Anpassen des Basisradius:**
1. Klicken Sie mit der rechten Maustaste auf eine Basis → **Radius anpassen**.
2. Geben Sie einen neuen Radius ein (50 %–1000 %).
3. Speichern Sie den Speicherstand im Spiel und laden Sie ihn erneut, damit die Strukturen neu zugewiesen werden können.

</details>





---




<div align="center">

## Fehlerbehebung

<img src="https://readme-typing-svg.demolab.com?lines=Wenn+die+Dinge+seitw%C3%A4rts+laufen;Keine+Panik;Wir+haben+alles+gesehen&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### „VCRUNTIME140.dll wurde nicht gefunden“ (Windows)

Installieren Sie den [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022).

### `struct.error` beim Parsen eines Speicherstands

Das Speicherdateiformat ist veraltet. Laden Sie den Speicherstand im Spiel (Solo, Koop oder Dedizierter Server) einmal, um eine automatische Strukturaktualisierung auszulösen, und versuchen Sie es dann erneut. Stellen Sie sicher, dass der Speicherstand mit oder nach dem neuesten Spiel-Patch aktualisiert wurde.

### GamePass Konverter funktioniert nicht

1. Schließen Sie die GamePass-Version von Palworld vollständig.
2. Warten Sie einige Minuten, bis die Dateihandles freigegeben werden.
3. Führen Sie den Konverter GamePass → Steam aus.
4. Starten Sie Palworld zur Überprüfung auf GamePass.

### Linux/MacOS-Binärdatei wird nicht gestartet

- **Linux:** `chmod +x PalworldSaveTools-*-linux`, um es als ausführbar zu markieren.
- **macOS:** Wenn vom Gatekeeper blockiert, klicken Sie mit der rechten Maustaste → **Öffnen** oder führen Sie `xattr -d com.apple.quarantine /path/to/app` aus.





---




<div align="center">

## Aufbau aus der Quelle

<img src="https://readme-typing-svg.demolab.com?lines=Kompilieren+Sie+es+selbst;Bauen+Sie+Ihr+eigenes;Von+der+Quelle+zur+Bin%C3%A4rdatei&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST unterstützt zwei Build-Pfade. Die CI/CD-Pipeline verwendet Nuitka für plattformübergreifende Release-Binärdateien; cx_Freeze wird für das lokale Windows-Installationsprogramm verwendet.

### Nuitka (Plattformübergreifend – Wird von CI/Releases verwendet)

Erfordert Python 3.11+ und `uv`. Nuitka wird automatisch installiert.

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

Ausgaben gehen an `dist/`:
- Windows → `dist/PalworldSaveTools-*.exe`
- Linux → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → verpackt als `.dmg`

### cx_Freeze (Windows Installer)

Für ein lokales Windows `.7z`-Paket:

```
scripts\build_cx.cmd
```

Dadurch wird `PST_standalone_v{version}.7z` im Projektstamm erstellt.

### Interaktiver Builder

Ein interaktives Menü zur Auswahl eines Build-Modus:

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## Mitwirken

<img src="https://readme-typing-svg.demolab.com?lines=M%C3%B6chten+Sie+helfen%3F+Hier+erfahren+Sie%2C+wie;Treten+Sie+dem+Team+bei;Jeder+Beitrag+z%C3%A4hlt&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Beiträge sind willkommen! Bitte senden Sie gerne einen Pull Request.

1. Forken Sie das Repository.
2. Erstellen Sie Ihren Feature-Zweig (`git checkout -b feature/AmazingFeature`).
3. Übernehmen Sie Ihre Änderungen (`git commit -m 'Add some AmazingFeature'`).
4. Drücken Sie auf den Zweig (`git push origin feature/AmazingFeature`).
5. Öffnen Sie eine Pull-Anfrage.





---




<div align="center">

## Haftungsausschluss

<img src="https://readme-typing-svg.demolab.com?lines=Lesen+Sie+dies%2C+bevor+Sie+etwas+kaputt+machen;Sie+wurden+gewarnt;Backup+zuerst%21;Mit+gro%C3%9Fer+Kraft...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>
**Die Verwendung dieses Tools erfolgt auf eigene Gefahr. Sichern Sie immer Ihre Sicherungsdateien, bevor Sie Änderungen vornehmen.**

Die Entwickler sind nicht verantwortlich für den Verlust gespeicherter Daten oder Probleme, die durch die Verwendung dieses Tools entstehen können.





---




<div align="center">

## Unterstützung

<img src="https://readme-typing-svg.demolab.com?lines=Wir+stehen+hinter+Ihnen;Brauchen+Sie+Hilfe%3F;Wir+sind+f%C3%BCr+Sie+da&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub Probleme:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Nexus-Mods:** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## Lizenz

<img src="https://readme-typing-svg.demolab.com?lines=MIT++%E2%80%93++tun+was+Sie+wollen;Kostenloses+Bier;Open+Source%2C+offener+Geist&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Dieses Projekt ist unter der MIT-Lizenz lizenziert – Einzelheiten finden Sie in der Datei [license](license).





---




<div align="center">

## Das Palworld-Team

<img src="https://readme-typing-svg.demolab.com?lines=Die+Menschen+hinter+der+Magie;Lernen+Sie+das+Team+kennen;Gebaut+mit+Leidenschaft&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Ohne die Menschen dahinter gäbe es dieses Projekt nicht.


### Active Maintainers

**[Pylar](https://github.com/deafdudecomputers)** — The man who started it all. Every line of this tool traces back to his vision and relentless work on the save engine, the GUI, and the features you use every day.

**[cyrix](https://github.com/CyrixJD115)** — Refactorer and sub-maintainer. Focused on code quality, simplification, and structural improvements — keeping the codebase clean, smaller, and easier to maintain as the project grows.

### Contributors

**[dkoz](https://github.com/dkoz)** — The man behind the IDs. Provides game data IDs, structural insight on the ID codes, and the deep knowledge of how Palworld's data is wired together that keeps the tool accurate with every game update.

**[oMaN-Rod](https://github.com/oMaN-Rod)** — Provided the original save parser that this project forked from. Without his foundational work on cracking the Palworld save format, none of this would exist. The fork streamlined and simplified his parser into what PST is today.

**[Okaetsu](https://github.com/Okaetsu)** — Modding insights that made base import/export possible. His understanding of how Palworld structures base data from the modding side bridged the gap between modding and save editing, making this feature a reality.









---




<div align="center">

## Danksagungen

<img src="https://readme-typing-svg.demolab.com?lines=Wo+Kredit+f%C3%A4llig+ist;Vielen+Dank+an+alle;Wir+stehen+auf+Schultern&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Ein großes Dankeschön an:

- **Palworld**, entwickelt von Pocketpair, Inc. – für das Spiel, das uns alle zusammengebracht hat.
- **Die Fehlerreporter** – jedes eingereichte Problem, jeder gefundene Grenzfall, jedes in Discord eingefügte Protokoll. Mit jedem Bericht machen Sie dieses Tool robuster.
- **Die Palworld-Modding-Community** – andere Modder, Tool-Entwickler und Tüftler, die Wissen teilen, Formate zurückentwickeln und das Ökosystem vorantreiben. Dieses Projekt steht auf den Schultern dieser gemeinsamen Anstrengung.
- **Alle Mitwirkenden und Community-Mitglieder** – egal, ob Sie eine PR eingereicht, eine Frage in Discord beantwortet oder einfach einem Freund von PST erzählt haben – vielen Dank.

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**Hergestellt mit ❤️ für die Palworld-Community**

[⬆ Back to Top](#palworld-save-tools)

</div>