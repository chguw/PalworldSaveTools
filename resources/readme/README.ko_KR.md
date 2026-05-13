<div align="center">

![PalworldSaveTools Logo](../PalworldSaveTools_Blue.png)

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

## 목차

- [기능](#기능)
- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [도구 개요](#도구-개요)
- [가이드](#가이드)
- [문제 해결](#문제-해결)
- [독립형 실행 파일 빌드(Windows에만 해당)](#독립형-실행-파일-빌드windows에만-해당)
- [기여](#기여)
- [라이센스](#라이센스)

---

## 기능

### 핵심 기능

| 기능 | 설명 |
|---------|-------------|
| **빠른 저장 구문 분석** | 사용 가능한 가장 빠른 저장 파일 리더 중 하나 |
| **플레이어 관리** | 보기, 편집, 이름 바꾸기, 레벨 변경, 기술 잠금 해제 및 플레이어 관리 |
| **길드 관리** | 플레이어 생성, 이름 변경, 이동, 실험실 연구 잠금 해제 및 길드 관리 |
| **Pal Editor** | 통계, 기술, IVs, 순위, 영혼, 성별, 보스/행운 토글에 대한 전체 편집기 |
| **베이스캠프 도구** | 내보내기, 가져오기, 복제, 반경 조정 및 기지 관리 |
| **맵 뷰어** | 좌표와 세부정보가 포함된 대화형 기지 및 플레이어 지도 |
| **캐릭터 이전** | 다른 월드/서버 간 캐릭터 전송(교차 저장) |
| **전환 저장** | Steam 및 GamePass 형식 간 변환 |
| **월드 설정** | WorldOption 및 LevelMeta 설정 편집 |
| **타임스탬프 도구** | 부정적인 타임스탬프 수정 및 플레이어 시간 재설정 |

### 올인원 도구

**올인원 도구** 제품군은 포괄적인 저장 관리 기능을 제공합니다.

- **삭제 도구**
  - 플레이어, 기지, 길드 삭제
  - 시간 임계값에 따라 비활성 플레이어 삭제
  - 중복 플레이어 및 빈 길드 제거
  - 참조되지 않거나 분리된 데이터 삭제

- **정리 도구**
  - 유효하지 않거나 수정된 항목 제거
  - 유효하지 않은 pals 및 passives 제거
  - 불법적인 pals 수정(법적 최대 통계로 제한)
  - 유효하지 않은 구조 제거
  - 대공 포탑 재설정
  - private chests 잠금 해제

- **길드 도구**
  - 모든 길드 재건
  - 길드 간 플레이어 이동
  - 플레이어 길드장 만들기
  - 길드 이름 바꾸기
  - 최대 길드 레벨
  - 모든 연구실 연구 잠금 해제

- **플레이어 도구**
  - 플레이어 pal 통계 및 기술 편집
  - 모든 기술 잠금 해제
  - 관찰 케이지 잠금 해제
  - 레벨 업/다운 플레이어
  - 플레이어 이름 바꾸기

- **유틸리티 저장**
  - 임무 재설정
  - 던전 초기화
  - 타임스탬프 수정
  - 과도하게 채워진 재고 정리
  - PalDefender 명령 생성

### 추가 도구

| 도구 | 설명 |
|------|-------------|
| **플레이어 편집 Pals** | 통계, 기술, IVs, 재능, 영혼, 순위 및 성별이 포함된 전체 pal editor |
| **SteamID 변환기** | Steam ID를 Palworld UID로 변환 |
| **호스트 저장 수정** | 두 플레이어 간 UID 교환(예: 호스트 교환) |
| **슬롯 인젝터** | 플레이어당 팔박스 슬롯 늘리기 |
| **지도 복원** | 모든 세계/서버에 잠금 해제된 지도 진행 상황 적용 |
| **세계 이름 바꾸기** | LevelMeta에서 세계 이름 변경 |
| **월드옵션 편집기** | 세계 설정 및 구성 편집 |
| **레벨메타 편집기** | 월드 메타데이터 편집(이름, 호스트, 레벨) |

---

## 설치

### 전제 조건

**독립형(Windows)의 경우:**
- 윈도우 10/11
- [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version) (2015-2022)

**소스에서 실행하는 경우(모든 플랫폼):**
- 파이썬 3.11 이상

### 독립 실행형(Windows - 권장)

1. [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)에서 최신 릴리스를 다운로드하세요.
2. zip 파일 추출
3. `PalworldSaveTools.exe`을 실행하세요.

### 소스에서(모든 플랫폼)

시작 스크립트는 자동으로 가상 환경을 생성하고 모든 종속성을 설치합니다.

**uv 사용:**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv venv --python 3.12
uv run start.py
```

**윈도우:**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
start_win.cmd
```

**리눅스:**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
chmod +x start_linux.sh
./start_linux.sh
```

### 지점

- **안정적**(권장): `git clone https://github.com/deafdudecomputers/PalworldSaveTools.git`
- **베타**(최신 기능): `git clone -b beta https://github.com/deafdudecomputers/PalworldSaveTools.git`

---

## 빠른 시작

1. **저장 파일 로드**
   - 헤더의 메뉴 버튼을 클릭하세요.
   - **저장 로드**를 선택합니다.
   - Palworld 저장 폴더로 이동하세요.
   - `Level.sav`을 선택하세요.

2. **데이터 탐색**
   - 탭을 사용하여 플레이어, 길드, 기지 또는 지도를 봅니다.
   - 특정 항목을 찾기 위한 검색 및 필터링

3. **변경**
   - 편집, 삭제, 수정할 항목을 선택하세요.
   - 추가 옵션이 있는 상황에 맞는 메뉴를 보려면 마우스 오른쪽 버튼을 클릭하세요.

4. **변경 사항 저장**
   - 메뉴 버튼 → **변경사항 저장**을 클릭합니다.
   - 백업이 자동으로 생성됩니다.

---

## 도구 개요

### 올인원 도구(AIO)

5개의 탭으로 구성된 포괄적인 저장 관리를 위한 기본 인터페이스:

**플레이어 인벤토리 탭** - 서버에 있는 모든 플레이어의 인벤토리를 보고 관리합니다.
- 플레이어 통계, 인벤토리, 장착 장비를 편집합니다.
- 품질을 편집하고, 인벤토리 및 장착된 장비에서 무엇이든 추가, 제거하는 기능.

**기지 인벤토리 탭** - 서버에 있는 모든 기지의 인벤토리를 보고 관리합니다.
- 기본 인벤토리를 편집합니다.
- 컨테이너를 지우고, 품질을 편집하고, 기본 인벤토리에서 무엇이든 추가하고 제거하는 기능.
- 부정 행위 가능성에 대한 필터링이 포함되어 있습니다.

**플레이어 탭** - 서버의 모든 플레이어를 보고 관리합니다.
- 플레이어 이름, 레벨 및 pal 카운트 편집
- 비활성 플레이어 삭제
- 플레이어 길드 및 마지막 온라인 시간 보기

**길드 탭** - 길드와 길드 기지를 관리합니다.
- 길드 이름 변경, 리더 변경
- 기본 위치 및 레벨 보기
- 비어 있거나 활동하지 않는 길드 삭제

**기지 탭** - 모든 베이스캠프 보기
- 기본 설계도 내보내기/가져오기
- 기지를 다른 길드에 복제
- 기본 반경 조정

### 맵 뷰어

세상의 대화형 시각화:
- 모든 기지 위치와 플레이어 위치 보기
- 길드 또는 플레이어 이름으로 필터링
- 자세한 정보를 보려면 마커를 클릭하세요.
- PalDefender용 `killnearestbase` 명령 생성

### 캐릭터 이전

다른 세계/서버 간 캐릭터 전송(교차 저장):
- 단일 또는 모든 플레이어 전송
- 캐릭터, pals, 인벤토리, 기술을 보존합니다.
- 협동 서버와 전용 서버 간 마이그레이션에 유용합니다.

### 호스트 저장 수정

두 플레이어 간에 UID를 교환합니다.
- 한 플레이어에서 다른 플레이어로 진행 상황 전송
- 호스트/Co-op에서 서버로 이전하는 데 필수적입니다.
- 플레이어 간 호스트 역할을 교환하는 데 유용합니다.
- 플랫폼 교체에 유용합니다(Xbox ← Steam)
- 호스트/서버 UID 할당 문제 해결
- **참고:** 영향을 받는 플레이어는 먼저 대상에 생성된 캐릭터를 저장해야 합니다.

---

## 가이드

### 저장 파일 위치

**호스트/협동조합:**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**전용 서버:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### 지도 잠금 해제

<details>
<summary>지도 잠금 해제 지침을 펼치려면 클릭하세요</summary>

1. `resources\`에서 `LocalData.sav`을 복사합니다.
2. 서버/월드 저장 폴더 찾기
3. 기존 `LocalData.sav`을 복사된 파일로 교체
4. 완전히 잠금 해제된 지도로 게임을 시작하세요.

> **참고:** 도구 탭의 **지도 복원** 도구를 사용하면 자동 백업을 통해 잠금 해제된 지도를 모든 월드/서버에 한 번에 적용할 수 있습니다.

</details>

### 호스트 → 서버 이전

<details>
<summary>호스트-서버 전송 가이드를 확장하려면 클릭하세요</summary>

1. 호스트 저장에서 `Level.sav` 및 `Players` 폴더를 복사합니다.
2. 전용서버 저장폴더에 붙여넣기
3. 서버 시작, 새 캐릭터 생성
4. 자동 저장을 기다린 후 닫습니다.
5. **Fix Host Save**를 사용하여 GUID를 마이그레이션합니다.
6. 파일을 다시 복사하고 실행하세요.

**수정 호스트 저장 사용:**
- 임시 폴더에서 `Level.sav`을 선택하세요.
- **기존 캐릭터** 선택(원본 저장에서)
- **새 캐릭터**(방금 생성한 캐릭터)를 선택하세요.
- **이전**을 클릭하세요.

</details>

### 호스트 스왑(호스트 변경)

<details>
<summary>호스트 스왑 가이드를 펼치려면 클릭하세요</summary>

**배경:**
- 호스트는 항상 `0001.sav`을 사용합니다. 호스트가 누구든 동일한 UID입니다.
- 각 클라이언트는 고유한 일반 UID 저장을 사용합니다(예: `123xxx.sav`, `987xxx.sav`).

**전제조건:**
두 플레이어(이전 호스트와 새 호스트) 모두 일반 저장을 생성해야 합니다. 이는 호스트의 세계에 합류하고 새로운 캐릭터를 생성함으로써 발생합니다.

**단계:**

1. **정기 저장이 있는지 확인**
   - 플레이어 A(이전 호스트)는 일반 저장을 가지고 있어야 합니다(예: `123xxx.sav`).
   - 플레이어 B(새 호스트)는 일반 저장을 가지고 있어야 합니다(예: `987xxx.sav`).

2. **이전 호스트의 호스트 저장을 일반 저장으로 교체**
   - PalworldSaveTools **Fix Host Save**를 사용하여 교체합니다.
   - 기존 호스트의 `0001.sav` → `123xxx.sav`
   - (이전 호스트의 진행 상황이 호스트 슬롯에서 일반 플레이어 슬롯으로 이동됩니다.)

3. **새 호스트의 일반 저장을 호스트 저장으로 전환**
   - PalworldSaveTools **Fix Host Save**를 사용하여 교체합니다.
   - 새로운 호스트의 `987xxx.sav` → `0001.sav`
   - (이것은 새로운 호스트의 진행 상황을 호스트 슬롯으로 이동시킵니다)

**결과:**
- 플레이어 B는 이제 `0001.sav`에서 자신의 캐릭터와 pals을 가진 호스트입니다.
- 플레이어 A는 `123xxx.sav`에서 원래 진행 상황으로 클라이언트가 됩니다.

</details>

### 기본 내보내기/가져오기

<details>
<summary>기본 내보내기/가져오기 가이드를 펼치려면 클릭하세요</summary>

**베이스 내보내기:**
1. PST에서 저장 내용을 로드합니다.
2. 기지 탭으로 이동
3. 베이스 우클릭 → 베이스 내보내기
4. `.json` 파일로 저장

**베이스 가져오기:**
1. 기지 탭 또는 기지 지도 뷰어로 이동합니다.
2. 거점을 가져오려는 길드를 마우스 오른쪽 버튼으로 클릭하세요.
3. 수입기지 선택
4. 내보낸 `.json` 파일을 선택하세요.

**베이스 복제:**
1. 베이스 우클릭 → 베이스 복제
2. 대상 길드 선택
3. 베이스는 오프셋 위치 지정을 통해 복제됩니다.

**베이스 반경 조정:**
1. 베이스를 우클릭 → 반경 조정
2. 새 반경을 입력합니다(50% - 1000%).
3. 구조를 재할당하려면 게임 내 저장 파일을 저장하고 로드하세요.

</details>

---

## 문제 해결

### "VCRUNTIME140.dll을 찾을 수 없습니다"

**해결책:** [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version) 설치

### `struct.error` 저장을 구문 분석할 때

**원인:** 오래된 저장 파일 형식

**해결책:**
1. 게임에서 저장 파일을 로드합니다(Solo, Coop 또는 Dedicated Server 모드).
2. 자동 구조 업데이트가 시작됩니다.
3. 최신 게임 패치 이후에 저장 내용이 업데이트되었는지 확인하세요.

### GamePass 변환기가 작동하지 않습니다

**해결책:**
1. Palworld의 GamePass 버전을 닫습니다.
2. 몇 분 정도 기다리세요
3. Steam → GamePass 변환기를 실행합니다.
4. GamePass에서 Palworld를 실행하여 확인하세요.

---

## 독립형 실행 파일 빌드(Windows에만 해당)

빌드 스크립트를 실행하여 독립 실행형 실행 파일을 만듭니다.

```bash
scripts\build.cmd
```

그러면 프로젝트 루트에 `PST_standalone_v{version}.7z`이 생성됩니다.

---

## 기여

기여를 환영합니다! 언제든지 Pull Request를 제출해 주세요.

1. 저장소 포크
2. 기능 브랜치 생성(`git checkout -b feature/AmazingFeature`)
3. 변경 사항을 커밋합니다. (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치로 푸시(`git push origin feature/AmazingFeature`)
5. 풀 리퀘스트 열기

---

## 면책조항

**이 도구를 사용할 때 발생하는 위험은 사용자 본인의 책임입니다. 수정하기 전에 항상 저장 파일을 백업하십시오.**

이 도구를 사용함으로써 발생할 수 있는 저장 데이터의 손실이나 문제에 대해 개발자는 책임을 지지 않습니다.

---

## 지원

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub 문제:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **문서:** [Wiki](https://github.com/deafdudecomputers/PalworldSaveTools/wiki) *(현재 개발 중)*

---

## 라이센스

이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 감사의 말씀

- **Palworld**는 Pocketpair, Inc.에서 개발했습니다.
- 이 도구를 개선하는 데 도움을 준 모든 기여자와 커뮤니티 구성원에게 감사드립니다.

---

<div align="center">

**Palworld 커뮤니티를 위해 ❤️으로 제작**

[⬆ Back to Top](#palworldsavetools)

</div>