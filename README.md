<div align="center">

![PalworldSaveTools Logo](resources/PalworldSaveTools_Blue.png)

# PalworldSaveTools

**A comprehensive save file editing toolkit for Palworld**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](README.md) | [简体中文](resources/readme/README.zh_CN.md) | [Deutsch](resources/readme/README.de_DE.md) | [Español](resources/readme/README.es_ES.md) | [Français](resources/readme/README.fr_FR.md) | [Русский](resources/readme/README.ru_RU.md) | [日本語](resources/readme/README.ja_JP.md) | [한국어](resources/readme/README.ko_KR.md)

---

### **Download the standalone version from [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)**

---

</div>

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Tools Overview](#tools-overview)
- [Guides](#guides)
- [Troubleshooting](#troubleshooting)
- [Building Standalone Executable](#building-standalone-executable-windows-only)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| **Fast Save Parsing** | One of the quickest save file readers available |
| **Player Management** | View, edit, rename, change level, unlock techs, and manage players |
| **Guild Management** | Create, rename, move players, unlock lab research, and manage guilds |
| **Pal Editor** | Full editor for stats, skills, IVs, rank, souls, gender, boss/lucky toggle |
| **Base Camp Tools** | Export, import, clone, adjust radius, and manage bases |
| **Map Viewer** | Interactive base and player map with coordinates and details |
| **Character Transfer** | Transfer characters between different worlds/servers (cross-save) |
| **Save Conversion** | Convert between Steam and GamePass formats |
| **World Settings** | Edit WorldOption and LevelMeta settings |
| **Timestamp Tools** | Fix negative timestamps and reset player times |

### All-in-One Tools

The **All-in-One Tools** suite provides comprehensive save management:

- **Deletion Tools**
  - Delete Players, Bases, or Guilds
  - Delete inactive players based on time thresholds
  - Remove duplicate players and empty guilds
  - Delete unreferenced/orphaned data

- **Cleanup Tools**
  - Remove invalid/modded items
  - Remove invalid pals and passives
  - Fix illegal pals (cap to legal max stats)
  - Remove invalid structures
  - Reset anti-air turrets
  - Unlock private chests

- **Guild Tools**
  - Rebuild All Guilds
  - Move players between guilds
  - Make player guild leader
  - Rename guilds
  - Max guild level
  - Unlock All Lab Research

- **Player Tools**
  - Edit player pal stats and skills
  - Unlock All Technologies
  - Unlock Viewing Cage
  - Level up/down players
  - Rename players

- **Save Utilities**
  - Reset missions
  - Reset dungeons
  - Fix timestamps
  - Trim overfilled inventories
  - Generate PalDefender commands

### Additional Tools

| Tool | Description |
|------|-------------|
| **Edit Player Pals** | Full pal editor with stats, skills, IVs, talents, souls, rank, and gender |
| **SteamID Converter** | Convert Steam IDs to Palworld UIDs |
| **Fix Host Save** | Swap UIDs between two players (e.g., for host swap) |
| **Slot Injector** | Increase palbox slots per player |
| **Restore Map** | Apply unlocked map progress across all worlds/servers |
| **Rename World** | Change world name in LevelMeta |
| **WorldOption Editor** | Edit world settings and configuration |
| **LevelMeta Editor** | Edit world metadata (name, host, level) |

---

## Installation

### Prerequisites

**For standalone (Windows):**
- Windows 10/11
- [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version) (2015-2022)

**For running from source (all platforms):**
- Python 3.11 or higher

### Standalone (Windows - Recommended)

1. Download the latest release from [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)
2. Extract the zip file
3. Run `PalworldSaveTools.exe`

### From Source (All Platforms)

The start scripts automatically create a virtual environment and install all dependencies.

**Using uv:**
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

### Branches

- **Stable** (recommended): `git clone https://github.com/deafdudecomputers/PalworldSaveTools.git`
- **Beta** (latest features): `git clone -b beta https://github.com/deafdudecomputers/PalworldSaveTools.git`

---

## Quick Start

1. **Load Your Save**
   - Click the menu button in the header
   - Select **Load Save**
   - Navigate to your Palworld save folder
   - Select `Level.sav`

2. **Explore Your Data**
   - Use the tabs to view Players, Guilds, Bases, or the Map
   - Search and filter to find specific entries

3. **Make Changes**
   - Select items to edit, delete, or modify
   - Right-click for context menus with additional options

4. **Save Your Changes**
   - Click the menu button → **Save Changes**
   - Backups are created automatically

---

## Tools Overview

### All-in-One Tools (AIO)

The main interface for comprehensive save management with five tabs:

**Player Inventory Tab** - View and manage all players' inventories on the server
- Edit player stats, inventory, equipped gear.
- Ability to edit quality, add, remove anything from inventory and equipped gear.

**Base Inventory Tab** - View and manage all bases' inventories on the server.
- Edit base inventory.
- Ability to clear containers, edit quality, add, remove anything from base inventories.
- Filtering included for any possiblities of cheating.

**Players Tab** - View and manage all players on the server
- Edit player names, levels, and pal counts
- Delete inactive players
- View player guilds and last online time

**Guilds Tab** - Manage guilds and their bases
- Rename guilds, change leaders
- View base locations and levels
- Delete empty or inactive guilds

**Bases Tab** - View all base camps
- Export/import base blueprints
- Clone bases to other guilds
- Adjust base radius

### Map Viewer

Interactive visualization of your world:
- View all base locations and player positions
- Filter by guild or player name
- Click markers for detailed information
- Generate `killnearestbase` commands for PalDefender

### Character Transfer

Transfer characters between different worlds/servers (cross-save):
- Transfer single or all players
- Preserves characters, pals, inventory, and technology
- Useful for migrating between co-op and dedicated servers

### Fix Host Save

Swap UIDs between two players:
- Transfer progress from one player to another
- Essential for host/co-op to server transfers
- Useful for swapping host role between players
- Useful for platform swaps (Xbox ↔ Steam)
- Resolves host/server UID assignment issues
- **Note:** Affected player must have a character created on the target save first

---

## Guides

### Save File Locations

**Host/Co-op:**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Dedicated Server:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Map Unlock

<details>
<summary>Click to expand map unlock instructions</summary>

1. Copy `LocalData.sav` from `resources\`
2. Find your server/world save folder
3. Replace the existing `LocalData.sav` with the copied file
4. Launch the game with a fully unlocked map

> **Note:** Use the **Restore Map** tool in the Tools tab to apply the unlocked map to ALL your worlds/servers at once with automatic backups.

</details>

### Host → Server Transfer

<details>
<summary>Click to expand host to server transfer guide</summary>

1. Copy `Level.sav` and `Players` folder from host save
2. Paste to dedicated server save folder
3. Start server, create a new character
4. Wait for auto-save, then close
5. Use **Fix Host Save** to migrate GUIDs
6. Copy files back and launch

**Using Fix Host Save:**
- Select the `Level.sav` from your temporary folder
- Choose the **old character** (from original save)
- Choose the **new character** (you just created)
- Click **Migrate**

</details>

### Host Swap (Changing Host)

<details>
<summary>Click to expand host swap guide</summary>

**Background:**
- Host always uses `0001.sav` — same UID for whoever hosts
- Each client uses a unique regular UID save (e.g., `123xxx.sav`, `987xxx.sav`)

**Prerequisites:**
Both players (old host and new host) must have their regular saves generated. This happens by joining the host's world and creating a new character.

**Steps:**

1. **Ensure Regular Saves Exist**
   - Player A (old host) should have a regular save (e.g., `123xxx.sav`)
   - Player B (new host) should have a regular save (e.g., `987xxx.sav`)

2. **Swap Old Host's Host Save to Regular Save**
   - Use PalworldSaveTools **Fix Host Save** to swap:
   - Old host's `0001.sav` → `123xxx.sav`
   - (This moves old host's progress from host slot to their regular player slot)

3. **Swap New Host's Regular Save to Host Save**
   - Use PalworldSaveTools **Fix Host Save** to swap:
   - New host's `987xxx.sav` → `0001.sav`
   - (This moves new host's progress into the host slot)

**Result:**
- Player B is now the host with their own character and pals in `0001.sav`
- Player A becomes a client with their original progress in `123xxx.sav`

</details>

### Base Export/Import

<details>
<summary>Click to expand base export/import guide</summary>

**Exporting a Base:**
1. Load your save in PST
2. Go to Bases tab
3. Right-click a base → Export Base
4. Save as `.json` file

**Importing a Base:**
1. Go to Bases tab or Base Map Viewer
2. Right-click on the Guild you want to import the base to
3. Select Import Base
4. Select your exported `.json` file

**Cloning a Base:**
1. Right-click a base → Clone Base
2. Select target guild
3. Base will be cloned with offset positioning

**Adjusting Base Radius:**
1. Right-click a base → Adjust Radius
2. Enter new radius (50% - 1000%)
3. Save and load the save in-game for structures to be reassigned

</details>

---

## Troubleshooting

### "VCRUNTIME140.dll was not found"

**Solution:** Install [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version)

### `struct.error` when parsing save

**Cause:** Outdated save file format

**Solution:**
1. Load the save in the game (Solo, Coop, or Dedicated Server mode)
2. This triggers an automatic structure update
3. Ensure the save was updated on or after the latest game patch

### GamePass converter not working

**Solution:**
1. Close the GamePass version of Palworld
2. Wait a few minutes
3. Run the Steam → GamePass converter
4. Launch Palworld on GamePass to verify

---

## Building Standalone Executable (Windows Only)

Run the build script to create a standalone executable:

```bash
scripts\build.cmd
```

This creates `PST_standalone_v{version}.7z` in the project root.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## Disclaimer

**Use this tool at your own risk. Always backup your save files before making any modifications.**

The developers are not responsible for any loss of save data or issues that may arise from using this tool.

---

## Support

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub Issues:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Documentation:** [Wiki](https://github.com/deafdudecomputers/PalworldSaveTools/wiki) *(Currently in development)*

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Palworld** developed by Pocketpair, Inc.
- Thanks to all contributors and community members who have helped improve this tool

---

<div align="center">

**Made with ❤️ for the Palworld community**

[⬆ Back to Top](#palworldsavetools)

</div>
