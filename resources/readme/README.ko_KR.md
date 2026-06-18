<div align="center">

![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Palworld를 위한 포괄적인 저장 파일 편집 툴킷**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

---

### ** [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** 에서 독립형 버전을 다운로드하세요

---

</div>
<div align="center">

## 개요

<img src="https://readme-typing-svg.demolab.com?lines=%2B%EC%A0%95%ED%99%95%ED%9E%88%20%2B%EC%9D%B4%EA%B2%8C%20%2B%EC%9D%B4%EA%B2%8C%20%2B%EB%AD%94%EA%B0%80%3F%3B%EB%8B%B9%EC%8B%A0%EC%9D%98%2B%EC%A0%80%EC%9E%A5%2C%2B%EB%8B%B9%EC%8B%A0%EC%9D%98%2B%EB%B0%A9%EB%B2%95%3B%ED%95%98%EB%82%98%2B%EB%8F%84%EA%B5%AC%2Bto%2B%EA%B7%9C%EC%B9%99%2B%EA%B7%B8%EB%93%A4%2B%EB%AA%A8%EB%91%90&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) is a fast, all-in-one desktop application for inspecting and editing Palworld save files. Python 및 PySide6으로 구축되어 게임의 압축된 저장 형식을 직접 읽고 씁니다. 게임 모드가 필요하지 않습니다.

전용 서버 관리, 협동 서버와 전용 서버 간 마이그레이션, 버려진 데이터 정리 또는 개별 Pals 미세 조정이 필요한 경우 PST는 모든 작업에 대해 단일 통합 인터페이스를 제공합니다.

### 하이라이트

- **교차 플랫폼** — **Windows**, **Linux** 및 **macOS**용으로 사전 구축된 바이너리입니다.
- **빠른 기본 구문 분석** — [`palsav`](src/palsav) 엔진으로 구동되는 사용 가능한 가장 빠른 저장 파일 리더 중 하나입니다.
- **시각적 지도** — 기지/플레이어 마커, 제외 구역 및 좌표 보정이 포함된 대화형 세계 지도입니다.
- **심층적인 Pal 편집** — 통계, IVs, 영혼, 기술, passives, 작업 적합성, 순위 및 외모 플래그를 완벽하게 제어할 수 있습니다.
- **서버급 도구** — 관리자를 위해 구축된 대량 삭제, 정리, 변환 및 문자 전송.
- **자동 백업** — 모든 저장 작업은 쓰기 전에 백업을 생성합니다.
- **8개 언어** — 현지화된 UI, 인앱 가이드 및 문서.





---





## 목차

- [개요](#개요)
- [기능](#기능)
- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [가이드](#가이드)
- [문제 해결](#문제-해결)
- [소스에서 빌드](#소스에서-빌드)
- [기여](#기여)
- [라이센스](#라이센스)
- [팔월드 팀](#팔월드-팀)

- [지원](#지원)
- [라이센스](#license)
- [감사의 말씀](#acknowledgements)





---




<div align="center">

## 기능

<img src="https://readme-typing-svg.demolab.com?lines=%EC%A2%8B%EC%9D%80%2B%EC%A2%8B%EC%9D%80%2B%EA%B2%83%EB%93%A4%3B%EC%B2%B4%ED%81%AC%2B%EC%9E%87%2B%EC%95%84%EC%9B%83%3B%ED%8F%AC%EC%9E%A5%2B%ED%8F%AC%ED%95%A8%2B%EB%8F%84%EA%B5%AC&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 플레이어 관리

- 이름, 레벨, pal 수, UID, 길드, 마지막 접속 시간을 기준으로 모든 플레이어를 보고 검색할 수 있습니다.
- 플레이어 이름, 레벨, 통계, 기술 포인트를 편집합니다.
- 여러 플레이어에 걸친 **대량 작업**: 아이템 관리, pal 관리 및 기술 잠금 해제.
- 시간 기준에 따라 비활성 플레이어를 삭제합니다. 중복을 제거하십시오.

### Pal Editor

모든 플레이어가 소유한 Pal에 대한 심층 편집 인터페이스입니다. Pals은 **파티**(활성 분대)와 **Palbox**(저장소)로 구성됩니다.

- **통계 및 IVs** — HP, 공격, 방어(IV 0–100), 레벨(1–80), 신뢰 순위(0–10).
- **소울** — HP, 공격, 방어, 제작 속도(0–20).
- **스킬** — 활성 스킬 선택기; 모든 동작을 배우십시오. Pals 전반에 걸친 대량 동기화 기술.
- **패시브 특성** — 전체 게임 데이터를 포함하는 패시브 선택기입니다.
- **작업 적합성** — 개별 작업 적합성 수준(0~10)을 설정합니다.
- **외모 플래그** — 보스/알파, 럭키/샤이니, 각성, 수입/DNA를 전환합니다.
- **순위 및 잠금** — 순위 및 즐겨찾기 잠금 수준(0~3)을 설정합니다.
- 새로운 Pals을 추가하거나 두 번 클릭하여 빠르게 삭제하세요.

### 길드 관리

2패널 보기: 상단에는 길드 목록, 하단에는 회원 명단이 표시됩니다.

- 길드 이름 바꾸기, 리더 변경, 길드 레벨 설정, 최대 길드 레벨 설정.
- 모든 연구실 연구를 잠금 해제하세요. 모든 길드를 재건하세요.
- 길드 간에 플레이어를 이동합니다. 비어 있거나 활동하지 않는 길드를 삭제하세요.

### 베이스캠프 도구

- 길드 연합이 있는 모든 베이스캠프를 볼 수 있습니다.
- 기본 청사진을 `.json`로 **내보내기**; **import** (single or multi-file) into any guild.
- 오프셋 위치 지정을 통해 다른 길드에 기지를 **복제**합니다.
- **기본 반경을 조정합니다**(50%~1000%).
- 비활성 기지와 기지가 아닌 지도 개체를 삭제합니다.

### 맵 뷰어

전체 세계를 대화형으로 시각화합니다.

- 세부 패널이 포함된 기본 마커(집 아이콘) 및 플레이어 마커(사람 아이콘).
- Toggle overlays: Bases, Players, Radius Rings, Exclusion Zones.
- **구역 그리기** — 지도에 직접 직사각형 또는 다각형 제외 구역을 그립니다.
- **Calibration mode** — Precisely align the map with game coordinates.
- 세계 지도 및 트리 지도 보기 길드나 플레이어 이름으로 필터링하세요.
- Zoom (1.0x–30.0x), pan, double-click to fly to a marker.
- 관리 작업을 위한 마커 및 빈 공간을 마우스 오른쪽 버튼으로 클릭합니다.

### 재고 관리

**플레이어 인벤토리** — 세 개의 하위 탭:
- *Inventory* — All items and equipment in the main bag; 수량 편집, 추가, 제거.
- *Key Items* — Quest items, effigies, and technology; 모든 조각상/핵심 항목을 대량 추가합니다.
- *Stats* — Level, HP, Stamina, Attack, Defense, Work Speed, Weight.
- Equipment panel for weapon, accessory, food, armor, shield, glider, and module slots.
- Unlock all map + fast-travel points in one click.

**Base Inventory** — Browse and manage items and working Pals across all bases:
- 컨테이너의 항목 보기/편집 투명한 용기; 컨테이너 슬롯을 수정합니다.
- 길드 간 아이템 작업(모든 길드에서 아이템 찾기/제거)
- 길드 간 구조 삭제.
- **기본 Pals** 하위 탭 — 전체 pal 편집기 상황에 맞는 메뉴를 사용하여 각 기지에 할당된 작업 Pals을 관리합니다.

### 제외

플레이어, 길드, 기지를 청소 작업으로부터 보호하는 보호 목록입니다.

- 3개의 나란히 있는 패널: 제외된 플레이어 UID, 길드 ID 및 기본 ID.
- 플레이어, 길드 또는 기지 탭에서 마우스 오른쪽 버튼 클릭 상황에 맞는 메뉴를 통해 항목을 추가합니다.
- 제외 목록을 지속적으로 저장하고 로드합니다.
- 대량 정리를 실행하기 **전에** 목록을 작성하세요.

### 저장 도구

**도구** 탭에서 클릭 가능한 카드로 액세스 가능:

| 도구 | 설명 |
|------|-------------|
| **저장 내용 변환** | SAV와 JSON 형식 간 변환 |
| **GamePass → Steam** 변환 | Xbox/GamePass 변환은 Steam 형식으로 저장 |
| **SteamID 변환** | Steam ID를 Palworld UID로 변환 |
| **지도 복원** | 모든 월드/서버에 완전히 잠금 해제된 지도 진행 상황 적용 |
| **슬롯 인젝터** | 플레이어당 팔박스 슬롯 늘리기 |
| **수정 저장** | 원시 저장 데이터 열기 및 수정 |
| **캐릭터 이전** | 다른 월드/서버 간 캐릭터 전송(교차 저장) |
| **호스트 저장 수정** | 두 플레이어 간 UID 교환(호스트 교환, 플랫폼 마이그레이션) |

### 정리 및 유틸리티 기능

**메뉴 → 기능**을 통해 액세스할 수 있는 이러한 서버급 작업에는 다음이 포함됩니다.

- **삭제** — 빈 길드, 비활성 기지/플레이어, 중복 플레이어, 참조되지 않은 데이터를 삭제합니다.
- **정리** — 유효하지 않은/수정된 항목, 유효하지 않은 pals 및 passives, 유효하지 않은 구조를 제거합니다. 불법적인 pals을 수정합니다(법적 최대값으로 제한). 대공 포탑을 재설정합니다. private chests 잠금 해제; 모든 구조물을 수리하십시오.
- **재설정** — 미션, 던전, 석유 굴착 장치, 침입자, 보급품 투하를 재설정합니다.
- **타임스탬프** — 부정적인 타임스탬프를 수정합니다. 플레이어 시간을 재설정합니다.
- **PalDefender** — `killnearestbase` 명령을 생성합니다.





---




<div align="center">

## 설치

<img src="https://readme-typing-svg.demolab.com?lines=%2Bit%2B%EC%8B%A4%ED%96%89%2B%EB%B6%84%20%EB%8B%A8%EC%9C%84%EB%A1%9C%20%EC%8B%A4%ED%96%89%3B%EB%8B%A4%EC%9A%B4%EB%A1%9C%EB%93%9C%2B%ED%95%98%EA%B3%A0%2B%EC%9D%B4%EB%8F%99%3B%EC%95%84%EB%8B%88%EC%9A%94%2B%EC%84%A4%EC%A0%95%2B%ED%95%84%EC%88%98&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 독립형 빌드(권장)

사전 빌드된 바이너리는 [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)의 세 가지 주요 플랫폼 모두에서 사용할 수 있습니다.

| 플랫폼 | 다운로드 | 요구사항 |
|------------|------------|-------------|
| **창** | `PalworldSaveTools-*.exe` | 윈도우 10/11, [VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)(2015~2022) |
| **리눅스** | `PalworldSaveTools-*-linux` | 모든 최신 배포판 |
| **맥OS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+(몬트레이 이상) |

[Nexus Mods](https://www.nexusmods.com/palworld/mods/3190)에서도 사용 가능합니다.

1. 귀하의 플랫폼에 적합한 빌드를 다운로드하십시오.
2. 실행 파일을 추출하고(보관된 경우) 실행합니다.
3. 그게 다입니다. Python이나 종속성이 필요하지 않습니다.

> **Windows:** "VCRUNTIME140.dll을 찾을 수 없습니다."라는 메시지가 표시되면 [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)을 설치하세요.

> **Linux:** 파일을 실행 가능으로 표시해야 할 수도 있습니다: `chmod +x PalworldSaveTools-*-linux`

> **macOS:** Gatekeeper가 앱을 차단하는 경우 마우스 오른쪽 버튼을 클릭하고 → **처음 열기**를 클릭하거나 `xattr -d com.apple.quarantine /path/to/app`을 실행하세요.

### 소스에서(모든 플랫폼)

PST는 종속성 관리를 위해 [`uv`](https://docs.astral.sh/uv/)을 사용합니다. 시작 스크립트는 자동으로 가상 환경을 생성하고 모든 것을 설치합니다.

**전제 조건:** [Python 3.11+](https://www.python.org/) 및 [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows**(더블클릭 실행 프로그램):
```
start.cmd
```

런처는 `.venv`을 생성하고, `uv sync`을 통해 종속성을 설치하고, 앱을 부팅합니다. 각 실행을 재현할 수 있도록 종료 시 잠금 파일을 정리합니다.





---




<div align="center">

## 빠른 시작

<img src="https://readme-typing-svg.demolab.com?lines=%EB%A1%9C%EB%93%9C.%2B%ED%8E%B8%EC%A7%91.%2B%EC%A0%80%EC%9E%A5.%2B%EA%B7%B8%EA%B1%B4%2B%EA%B0%84%EB%8B%A8%ED%95%A9%EB%8B%88%EB%8B%A4.%3B%EC%84%B8%2B%EA%B3%84%EB%8B%A8%2Bto%2B%EC%98%81%EA%B4%91%3B%2B%EA%B7%B8%EB%A0%87%EA%B2%8C%20%2B%EC%89%BD%EB%8B%A4&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **저장 파일 로드**
   - **메뉴 → 저장 로드**를 클릭하거나 `.sav` 파일을 창에 끌어다 놓습니다.
   - Palworld 저장 폴더로 이동하여 `Level.sav`을 선택하세요.

2. **데이터 탐색**
   - **지도**, **도구**, **플레이어**, **길드**, **기지**, **플레이어 인벤토리**, **베이스 인벤토리**, **Pal Editor**, **제외** 탭을 사용하여 저장 내용을 살펴보세요.
   - 통계 표시줄에는 실시간 카운트가 표시됩니다. 빠른 탐색 아이콘은 각 섹션으로 이동합니다.

3. **변경**
   - 선택하려면 마우스 왼쪽 버튼을 클릭하세요. 상황에 맞는 작업을 수행하려면 거의 모든 것을 마우스 오른쪽 버튼으로 클릭하세요.
   - 더블클릭하면 빠른 편집, 빠른 삭제가 가능합니다. (자세한 내용은 앱 내 가이드를 참고하세요.)

4. **변경 사항 저장**
   - **메뉴 → 변경사항 저장**을 클릭합니다. 백업은 자동으로 생성됩니다.

> **팁:** 각 탭에는 기본 제공 가이드가 있습니다. 탭에서 수행할 수 있는 작업을 정확히 보려면 ​​탭에서 도움말 아이콘을 클릭하세요. 더 자세한 내용을 보려면 **버튼, 필드 또는 컨트롤 위로 마우스를 가져가면** 헤더에 자세한 툴팁이 표시됩니다. 앱 내 도구 설명 도움말 시스템은 모든 기능의 기능과 사용 방법을 정확히 이해하는 데 가장 적합한 참고 자료입니다.





---




<div align="center">

## 가이드

<img src="https://readme-typing-svg.demolab.com?lines=%EB%8B%A8%EA%B3%84%EB%B3%84%2B%EC%97%B0%EC%8A%B5%3B%2Bthe%2B%EA%B0%80%EC%9D%B4%EB%93%9C%EB%A5%BC%20%EB%94%B0%EB%A5%B4%EC%84%B8%EC%9A%94%3B%EC%9A%B0%EB%A6%AC%EB%8A%94%2B%EB%B3%B4%EC%97%AC%EC%A4%84%2B%EB%8B%B9%EC%8B%A0%EC%97%90%EA%B2%8C%2B%EB%B0%A9%EB%B2%95%EC%9D%84%2B%EB%B3%B4%EC%97%AC%EC%A4%84%20%EA%B2%83%EC%9E%85%EB%8B%88%EB%8B%A4&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 저장 파일 위치

**호스트/협동조합(Windows):**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**전용 서버:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### 지도 잠금 해제

PST는 저장을 위해 전체 지도(모든 빠른 이동 지점)를 잠금 해제할 수 있습니다.

1. PST로 저장 내용을 로드합니다.
2. **플레이어 인벤토리** 탭을 열고 단일 플레이어의 경우 **모든 지도 잠금 해제 + 빠른 이동**을 클릭합니다. **또는**
3. 도구 탭의 **지도 복원** 도구를 사용하여 **모든** 월드/서버에 잠금 해제된 지도 진행 상황을 한 번에 적용합니다.
4. 변경 사항을 저장합니다. 자동 백업이 생성됩니다.

### 호스트 → 서버 이전

<details>
<summary>확대하려면 클릭하세요</summary>

1. 호스트 저장에서 `Level.sav` 및 `Players` 폴더를 복사합니다.
2. 전용서버 저장 폴더에 붙여넣으세요.
3. 서버를 시작하고 새 캐릭터를 생성한 후 자동 저장을 기다립니다.
4. 서버를 닫습니다.
5. PST에서 **Fix Host Save**를 사용하여 기존 캐릭터의 GUID를 새 캐릭터로 마이그레이션합니다.
6. 파일을 다시 복사하고 서버를 시작합니다.

</details>

### 호스트 스왑(호스트 변경)

<details>
<summary>확대하려면 클릭하세요</summary>

**배경:** 호스트는 항상 호스트 누구에게나 동일한 UID인 `0001.sav` 슬롯을 사용합니다. 각 클라이언트는 고유한 일반 저장을 얻습니다(예: `123xxx.sav`).

**전제 조건:** 이전 호스트와 새 호스트 모두 캐릭터 가입 및 생성을 통해 생성된 일반 저장이 있어야 합니다.

**단계:**

1. **Fix Host Save**를 사용하여 기존 호스트의 `0001.sav` → 일반 저장(예: `123xxx.sav`)을 교체합니다. 그러면 진행 상황이 호스트 슬롯 밖으로 이동됩니다.
2. **Fix Host Save**를 사용하여 새 호스트의 일반 저장(예: `987xxx.sav`) → `0001.sav`을 교체합니다. 그러면 진행 상황이 호스트 슬롯으로 이동됩니다.

**결과:** 이제 새 호스트는 자신의 캐릭터와 Pals로 `0001.sav`을 차지합니다. 이전 호스트는 원래 진행 상황을 그대로 유지하면서 클라이언트가 됩니다.

</details>

### 캐릭터 이전(교차저장)

<details>
<summary>확대하려면 클릭하세요</summary>

캐릭터, Pals, 인벤토리 및 기술을 보존하면서 다른 세계나 서버 간에 캐릭터를 전송하세요.

1. 도구 탭에서 **캐릭터 이전** 도구를 엽니다.
2. 원본 저장과 대상 저장을 선택하세요.
3. 단일 플레이어 또는 모든 플레이어를 이적합니다.
4. 협동 서버와 전용 서버 간 마이그레이션에 유용합니다.

</details>

### 기본 내보내기/가져오기/복제

<details>
<summary>확대하려면 클릭하세요</summary>

**베이스 내보내기:**
1. **기지** 탭으로 이동합니다(또는 Map Viewer를 사용합니다).
2. 베이스를 마우스 오른쪽 버튼으로 클릭 → **베이스 내보내기**.
3. `.json` 청사진 파일로 저장합니다.

**베이스 가져오기:**
1. 대상 길드(거점 탭, 맵 뷰어, 길드 탭)를 마우스 오른쪽 버튼으로 클릭하세요.
2. **베이스 가져오기**(단일 파일) 또는 **베이스 가져오기(다중 파일)**를 선택합니다.
3. 내보낸 `.json` 파일을 선택합니다.

**베이스 복제:**
1. 베이스를 마우스 오른쪽 버튼으로 클릭 → **베이스 복제**.
2. 대상 길드를 선택하세요.
3. 오프셋 위치 지정을 통해 베이스가 복제됩니다.

**베이스 반경 조정:**
1. 베이스를 마우스 오른쪽 버튼으로 클릭 → **반경 조정**.
2. 새 반경(50%~1000%)을 입력합니다.
3. 구조를 재할당하려면 게임 내 저장 내용을 저장하고 다시 로드하세요.

</details>





---




<div align="center">

## 문제 해결

<img src="https://readme-typing-svg.demolab.com?lines=%EC%96%B8%EC%A0%9C%2B%EC%82%AC%EB%AC%BC%EC%9D%B4%2B%EA%B0%80%EB%8B%A4%2B%EC%98%86%EC%9C%BC%EB%A1%9C%3B%EB%8B%B9%ED%99%A9%ED%95%98%EC%A7%80%20%EB%A7%88%EC%84%B8%EC%9A%94%3B%EC%9A%B0%EB%A6%AC%EB%8A%94%2B%EB%B3%B8%2B%EA%B7%B8%EA%B2%83%2B%EB%AA%A8%EB%91%90%EB%A5%BC%20%EB%B3%B4%EC%95%98%EC%8A%B5%EB%8B%88%EB%8B%A4&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### "VCRUNTIME140.dll을 찾을 수 없습니다."(Windows)

[Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)(2015~2022)을 설치합니다.

### `struct.error` 저장 파일을 분석할 때

저장 파일 형식이 오래되었습니다. 자동 구조 업데이트를 실행하려면 게임 내 저장 파일(솔로, 협동 또는 전용 서버)을 한 번 로드한 후 다시 시도하세요. 최신 게임 패치나 그 이후에 저장 내용이 업데이트되었는지 확인하세요.

### GamePass 변환기가 작동하지 않습니다

1. Palworld의 GamePass 버전을 완전히 닫습니다.
2. 파일 핸들이 해제될 때까지 몇 분 정도 기다립니다.
3. GamePass → Steam 변환기를 실행합니다.
4. GamePass에서 Palworld를 실행하여 확인하세요.

### Linux/macOS 바이너리가 실행되지 않습니다.

- **Linux:** `chmod +x PalworldSaveTools-*-linux` 실행 가능으로 표시합니다.
- **macOS:** Gatekeeper에 의해 차단된 경우 마우스 오른쪽 버튼을 클릭하고 → **열기**를 클릭하거나 `xattr -d com.apple.quarantine /path/to/app`을 실행하세요.





---




<div align="center">

## 소스에서 빌드

<img src="https://readme-typing-svg.demolab.com?lines=%EC%BB%B4%ED%8C%8C%EC%9D%BC%2B%EA%B7%B8%EA%B2%83%2B%EC%A7%81%EC%A0%91%3B%2B%EB%82%98%EB%A7%8C%EC%9D%98%20%2B%20%EB%82%98%EB%A7%8C%EC%9D%98%20%EB%B9%8C%EB%93%9C%3BFrom%2B%EC%86%8C%EC%8A%A4%2Bto%2B%EB%B0%94%EC%9D%B4%EB%84%88%EB%A6%AC&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST는 두 가지 빌드 경로를 지원합니다. CI/CD 파이프라인은 크로스 플랫폼 릴리스 바이너리에 Nuitka를 사용합니다. cx_Freeze는 로컬 Windows 설치 프로그램에 사용됩니다.

### Nuitka(교차 플랫폼 — CI/릴리스에서 사용)

Python 3.11+ 및 `uv`이 필요합니다. Nuitka는 자동으로 설치됩니다.

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

출력은 `dist/`로 이동합니다.
- 윈도우 → `dist/PalworldSaveTools-*.exe`
- 리눅스 → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → `.dmg`로 패키징됨

### cx_Freeze(Windows 설치 프로그램)

로컬 Windows `.7z` 패키지의 경우:

```
scripts\build_cx.cmd
```

그러면 프로젝트 루트에 `PST_standalone_v{version}.7z`이 생성됩니다.

### 인터랙티브 빌더

빌드 모드를 선택하는 대화형 메뉴:

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## 기여

<img src="https://readme-typing-svg.demolab.com?lines=%2B%EB%8F%84%EC%9B%80%EC%9D%84%20%2B%EC%9B%90%ED%95%98%EC%8B%AD%EB%8B%88%EA%B9%8C%3F%2B%EC%97%AC%EA%B8%B0%EC%97%90%2B%EB%B0%A9%EB%B2%95%EC%9D%B4%20%EC%9E%88%EC%8A%B5%EB%8B%88%EB%8B%A4.%3B%2B%ED%8C%80%EC%97%90%20%ED%95%A9%EB%A5%98%ED%95%98%EC%84%B8%EC%9A%94%3B%EB%AA%A8%EB%93%A0%2B%EA%B8%B0%EC%97%AC%2B%EC%B9%B4%EC%9A%B4%ED%8A%B8&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

기여를 환영합니다! 언제든지 Pull Request를 제출해 주세요.

1. 저장소를 포크하십시오.
2. 기능 분기(`git checkout -b feature/AmazingFeature`)를 만듭니다.
3. 변경 사항을 커밋합니다(`git commit -m 'Add some AmazingFeature'`).
4. 분기(`git push origin feature/AmazingFeature`)로 푸시합니다.
5. 끌어오기 요청을 엽니다.





---




<div align="center">

## 면책조항

<img src="https://readme-typing-svg.demolab.com?lines=%2B%EC%9D%B4%20%2B%EB%8B%B9%EC%8B%A0%EC%9D%B4%2B%ED%9C%B4%EC%8B%9D%2B%EB%AC%B4%EC%97%87%EC%9D%84%20%ED%95%98%EA%B8%B0%20%EC%A0%84%EC%97%90%2B%EC%9D%B4%EA%B2%83%EC%9D%84%20%EC%9D%BD%EC%9C%BC%EC%84%B8%EC%9A%94%3B%EB%8B%B9%EC%8B%A0%EC%9D%80%2B%EA%B2%BD%EA%B3%A0%EB%A5%BC%20%EB%B0%9B%EC%95%98%EC%8A%B5%EB%8B%88%EB%8B%A4%3B%EB%B0%B1%EC%97%85%2B%EC%B2%AB%EB%B2%88%EC%A7%B8%21%3B%2B%EC%9C%84%EB%8C%80%ED%95%9C%20%2B%ED%9E%98%EC%9C%BC%EB%A1%9C...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>
**이 도구를 사용할 때 발생하는 위험은 사용자 본인의 책임입니다. 수정하기 전에 항상 저장 파일을 백업하십시오.**

이 도구를 사용함으로써 발생할 수 있는 저장 데이터의 손실이나 문제에 대해 개발자는 책임을 지지 않습니다.





---




<div align="center">

## 지원

<img src="https://readme-typing-svg.demolab.com?lines=%EC%9A%B0%EB%A6%AC%EB%8A%94%20%2B%EB%8B%B9%EC%8B%A0%EC%9D%98%20%2B%EB%A5%BC%20%EB%90%98%EC%B0%BE%EC%95%98%EC%8A%B5%EB%8B%88%EB%8B%A4%3B%EB%8F%84%EC%9B%80%EC%9D%B4%20%ED%95%84%EC%9A%94%ED%95%98%EC%8B%A0%EA%B0%80%EC%9A%94%3F%3B%EC%9A%B0%EB%A6%AC%EB%8A%94%2B%EB%8B%B9%EC%8B%A0%EC%9D%84%20%EC%9C%84%ED%95%B4%2B%EC%97%AC%EA%B8%B0%EC%97%90%20%EC%9E%88%EC%8A%B5%EB%8B%88%EB%8B%A4&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub 문제:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Nexus 모드:** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## 라이센스

<img src="https://readme-typing-svg.demolab.com?lines=MIT%2B%E2%80%94%2B%EB%AC%B4%EC%97%87%EC%9D%B4%EB%93%A0%2B%EB%8B%B9%EC%8B%A0%EC%9D%B4%2B%EC%9B%90%ED%95%98%EB%8A%94%20%EC%9D%BC%EC%9D%84%2B%ED%95%98%EC%84%B8%EC%9A%94%3B%EB%AC%B4%EB%A3%8C%2B%EC%9D%8C%EB%A3%8C%2B%EB%A7%A5%EC%A3%BC%3B%EC%98%A4%ED%94%88%2B%EC%86%8C%EC%8A%A4%2C%2B%EC%98%A4%ED%94%88%2B%EB%A7%88%EC%9D%B8%EB%93%9C&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다. 자세한 내용은 [license](license) 파일을 참조하세요.





---




<div align="center">

## 팔월드 팀

<img src="https://readme-typing-svg.demolab.com?lines=%2B%EB%A7%88%EB%B2%95%20%EB%92%A4%EC%97%90%20%2B%EC%82%AC%EB%9E%8C%EB%93%A4%20%2B%EB%92%A4%EC%97%90%20%EC%9E%88%EB%8A%94%20%EC%82%AC%EB%9E%8C%EB%93%A4%3B%EB%A7%8C%EB%82%98%EB%8B%A4%2Bthe%2B%ED%8C%80%3B%EA%B5%AC%EC%B6%95%20%2B%20%EC%97%B4%EC%A0%95%20%2B%20%EC%97%B4%EC%A0%95&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

이 프로젝트는 뒤에 있는 사람들이 없었다면 존재하지 않았을 것입니다.

**[Pylar](https://github.com/deafdudecomputers)** — 모든 것을 시작한 사람. 이 도구의 모든 라인은 저장 엔진, GUI 및 매일 사용하는 기능에 대한 그의 비전과 끊임없는 작업으로 거슬러 올라갑니다.

**[cyrix](https://github.com/CyrixJD115)** — 리팩터러 및 하위 유지관리자. 코드 품질, 단순화 및 구조적 개선에 중점을 두고 프로젝트가 성장함에 따라 코드베이스를 깔끔하고 작게 유지하고 유지 관리하기 쉽게 만듭니다.

**[dkoz](https://github.com/dkoz)** — ID 뒤에 있는 남자. 게임 데이터 ID, ID 코드에 대한 구조적 통찰력, 모든 게임 업데이트에서 도구의 정확성을 유지하기 위해 Palworld의 데이터가 어떻게 연결되어 있는지에 대한 깊은 지식을 제공합니다.

**[oMaN-Rod](https://github.com/oMaN-Rod)** — 이 프로젝트가 분기된 원본 저장 파서를 제공했습니다. Palworld 저장 형식을 해독하는 그의 기초적인 작업이 없었다면 이 중 어떤 것도 존재하지 않았을 것입니다. 포크는 파서를 오늘날의 PST로 간소화하고 단순화했습니다.


**[Okaetsu](https://github.com/Okaetsu)** — The modding mind behind base import/export. His deep understanding of how Palworld structures base data from the modding side was instrumental in getting this feature right. Without his insights bridging the gap between modding and save editing, base import/export would not have been possible.




---




<div align="center">

## 감사의 말씀

<img src="https://readme-typing-svg.demolab.com?lines=%2B%EC%8B%A0%EC%9A%A9%2B%EA%B8%B0%ED%95%9C%EC%9D%B4%20%EC%9E%88%EB%8A%94%20%EA%B3%B3%3B%EA%B0%90%EC%82%AC%ED%95%A9%EB%8B%88%EB%8B%A4%2B%EA%B0%90%EC%82%AC%ED%95%A9%EB%8B%88%EB%8B%A4%2B%EB%AA%A8%EB%91%90%3B%EC%9A%B0%EB%A6%AC%EB%8A%94%2B%EC%84%9C%EC%84%9C%2B%EC%96%B4%EA%B9%A8%EB%A5%BC%20%EB%94%9B%EA%B3%A0&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

다음 분들께 큰 감사를 드립니다:

- **Palworld**는 Pocketpair, Inc.에서 개발했습니다. — 우리 모두를 하나로 모으는 게임을 위해.
- **버그 보고자** — 제출된 모든 문제, 발견된 모든 극단적인 사례, Discord에 붙여넣은 모든 로그. 각 보고서를 통해 이 도구를 더욱 강력하게 만들 수 있습니다.
- **Palworld 모딩 커뮤니티** — 지식, 리버스 엔지니어링 형식을 공유하고 생태계를 발전시키는 동료 모더, 도구 개발자 및 땜장이입니다. 이 프로젝트는 그러한 공동 노력의 어깨 위에 서 있습니다.
- **모든 기여자와 커뮤니티 회원** — PR을 제출했든, Discord의 질문에 답변했든, 아니면 단순히 친구에게 PST에 대해 이야기했든 — 감사합니다.

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**Palworld 커뮤니티를 위해 ❤️으로 제작**

[⬆ Back to Top](#palworld-save-tools)

</div>