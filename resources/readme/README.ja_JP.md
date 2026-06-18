<div align="center">

![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Palworld 用の包括的なセーブファイル編集ツールキット**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

---

### **スタンドアロン バージョンを [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** からダウンロードします

---

</div>
<div align="center">

## 概要

<img src="https://readme-typing-svg.demolab.com?lines=%E3%81%93%E3%82%8C%E3%81%A8%E3%81%AF%2B%E6%AD%A3%E7%A2%BA%E3%81%AB%E3%81%AF%2B%E4%BD%95%E3%81%A7%E3%81%99%E3%81%8B%3F%3B%E3%81%82%E3%81%AA%E3%81%9F%2B%E4%BF%9D%E5%AD%98%E3%80%81%2B%E3%81%82%E3%81%AA%E3%81%9F%2B%E6%96%B9%E6%B3%95%3B1%20%E3%81%A4%2B%E3%83%84%E3%83%BC%E3%83%AB%2Bto%2B%E3%83%AB%E3%83%BC%E3%83%AB%2B%E3%81%9D%E3%82%8C%E3%82%89%2B%E3%81%99%E3%81%B9%E3%81%A6&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) は、Palworld セーブ ファイルを検査および編集するための高速なオールインワン デスクトップ アプリケーションです。 Python と PySide6 で構築されており、ゲームの圧縮保存形式を直接読み書きします。ゲーム MOD は必要ありません。

専用サーバーの管理、生協サーバーと専用サーバー間の移行、放棄されたデータのクリーンアップ、または個々の Pals の微調整が必​​要な場合でも、PST はそのすべてに単一の統合インターフェイスを提供します。

### ハイライト

- **クロスプラットフォーム** — **Windows**、**Linux**、および **macOS** 用の事前構築済みバイナリ。
- **高速ネイティブ解析** — [`palsav`](src/palsav) エンジンを搭載した、利用可能な中で最も高速な保存ファイル リーダーの 1 つ。
- **ビジュアルマップ** — ベース/プレイヤーマーカー、除外ゾーン、座標キャリブレーションを備えたインタラクティブなワールドマップ。
- **詳細な Pal 編集** — ステータス、IVs、魂、スキル、passives、仕事の適性、ランク、および外観フラグを完全に制御します。
- **サーバーグレードのツール** — 管理者向けに構築された一括削除、クリーンアップ、変換、文字転送。
- **自動バックアップ** - すべての保存操作で、書き込み前にバックアップが作成されます。
- **8 言語** — ローカライズされた UI、アプリ内ガイド、ドキュメント。





---





## 目次

- [概要](#概要)
- [特徴](#特徴)
- [インストール](#インストール)
- [クイックスタート](#クイックスタート)
- [ガイド](#ガイド)
- [トラブルシューティング](#トラブルシューティング)
- [ソースからのビルド](#ソースからのビルド)
- [貢献する](#貢献する)
- [ライセンス](#ライセンス)
- [パルワールドチーム](#パルワールドチーム)

- [サポート](#support)
- [ライセンス](#license)
- [謝辞](#acknowledgments)





---




<div align="center">

## 特徴

<img src="https://readme-typing-svg.demolab.com?lines=%2B%E8%89%AF%E3%81%84%E3%82%82%E3%81%AE%2B%E3%82%82%E3%81%AE%3B%E3%83%81%E3%82%A7%E3%83%83%E3%82%AF%2B%E3%82%A4%E3%83%83%E3%83%88%2B%E3%82%A2%E3%82%A6%E3%83%88%3B%E6%A2%B1%E5%8C%85%2B%E4%BB%98%E5%B1%9E%2B%E3%83%84%E3%83%BC%E3%83%AB&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### プレーヤーの管理

- 名前、レベル、pal カウント、UID、ギルド、最後に見た時間によってすべてのプレイヤーを表示および検索します。
- プレイヤー名、レベル、ステータス、テクノロジーポイントを編集します。
- 複数のプレイヤーにわたる **一括操作**: アイテム管理、pal 管理、テクノロジーのロック解除。
- 時間のしきい値に従って非アクティブなプレイヤーを削除します。重複を削除します。

### Pal Editor

あらゆるプレーヤーが所有するあらゆる Pal のための詳細な編集インターフェイス。 Pals は **Party** (アクティブ チーム) と **Palbox** (ストレージ) によって組織されます。

- **ステータスと IVs** — HP、攻撃力、防御力 (IV 0 ～ 100)、レベル (1 ～ 80)、信頼ランク (0 ～ 10)。
- **ソウル** — HP、攻撃力、防御力、クラフト速度 (0–20)。
- **スキル** — アクティブなスキルピッカー。すべての動きを学びます。 Pals 全体でスキルを一括同期します。
- **パッシブ特性** — 完全なゲームデータを備えたパッシブピッカー。
- **作業適性** — 個別の作業適性レベル (0 ～ 10) を設定します。
- **外観フラグ** — ボス/アルファ、ラッキー/シャイニー、覚醒、インポート/DNAを切り替えます。
- **ランクとロック** — ランクとお気に入りのロック レベル (0 ～ 3) を設定します。
- 新しい Pals を追加するか、ダブルクリックして簡単に削除します。

### ギルド管理

2 つのパネル ビュー: 上部にギルド リスト、下部にメンバー名簿。

- ギルドの名前変更、リーダーの変更、ギルドレベルの設定、最大ギルドレベル。
- すべての研究室の研究のロックを解除します。すべてのギルドを再構築します。
- ギルド間でプレイヤーを移動します。空のギルドまたは非アクティブなギルドを削除します。

### ベースキャンプツール

- ギルド関連付けのあるすべてのベースキャンプを表示します。
- **基本ブループリントを `.json` にエクスポート**します。 **インポート** (単一または複数のファイル) を任意のギルドにインポートします。
- **基地をオフセット配置で他のギルドにクローン**します。
- **ベース半径を調整** (50% ～ 1000%)。
- 非アクティブなベースおよび非ベース マップ オブジェクトを削除します。

### マップビューア

あなたの世界全体をインタラクティブに視覚化します。

- 詳細パネルを備えたベース マーカー (家のアイコン) とプレーヤー マーカー (人のアイコン)。
- オーバーレイの切り替え: ベース、プレーヤー、半径リング、除外ゾーン。
- **ゾーン描画** — 長方形または多角形の除外ゾーンをマップ上に直接描画します。
- **キャリブレーション モード** — マップをゲーム座標に正確に合わせます。
- ワールドマップとツリーマップビュー;ギルドまたはプレイヤー名でフィルターします。
- ズーム (1.0x ～ 30.0x)、パン、ダブルクリックしてマーカーに移動します。
- 管理アクション用のマーカーと空きスペースを右クリックします。

### 在庫管理

**プレーヤー インベントリ** — 3 つのサブタブ:
- *在庫* — メインバッグ内のすべてのアイテムと装備。数量を編集、追加、削除します。
- *キーアイテム* — クエストアイテム、人形、テクノロジー。すべてのフィギュア/キーアイテムを一括追加します。
- *ステータス* — レベル、HP、スタミナ、攻撃力、防御力、作業速度、体重。
- 武器、アクセサリー、食料、防具、盾、グライダー、モジュールスロットの装備パネル。
- ワンクリックですべてのマップとファストトラベルポイントのロックを解除します。

**拠点在庫** — すべての拠点にわたるアイテムと作業 Pals を参照および管理します。
- コンテナ内のアイテムを表示/編集します。透明な容器。コンテナのスロットを変更します。
- ギルド間のアイテム操作 (すべてのギルドにわたるアイテムの検索/削除)。
- ギルド間の構造の削除。
- **ベース Pals** サブタブ — 完全な pal エディター コンテキスト メニューを使用して、各ベースに割り当てられた作業中の Pals を管理します。

### 除外事項

プレイヤー、ギルド、基地を掃討作戦から守る保護リスト。

- 3 つの横に並んだパネル: 除外されたプレーヤー UID、ギルド ID、およびベース ID。
- [プレイヤー]、[ギルド]、または [拠点] タブで右クリックしてコンテキスト メニューを使用してエントリを追加します。
- 除外リストを永続的に保存およびロードします。
- 一括クリーンアップを実行する**前**にリストを作成します。

### 保存ツール

[**ツール**] タブからクリック可能なカードとしてアクセスできます。

|ツール |説明 |
|------|---------------|
| **保存の変換** | SAV 形式と JSON 形式の間で変換する |
| **GamePass → Steam** に変換 | Xbox/GamePass セーブを Steam 形式に変換する |
| **SteamID を変換** | Steam ID を Palworld UID に変換する |
| **マップを復元** |完全にロック解除されたマップの進行状況をすべてのワールド/サーバーに適用します。
| **スロット インジェクター** |プレイヤーごとの Palbox スロットを増やす |
| **変更保存** |生のセーブデータを開いて変更する |
| **キャラクター転送** |異なるワールド/サーバー間でキャラクターを転送する (クロスセーブ) |
| **ホストの保存を修正** | 2 つのプレーヤー間で UID を交換する (ホスト交換、プラットフォーム移行) |

### クリーンアップとユーティリティ関数

**[メニュー] → [機能]** からアクセスでき、これらのサーバー グレードの操作には次のものが含まれます。

- **削除** — 空のギルド、非アクティブな拠点/プレイヤー、重複したプレイヤー、参照されていないデータを削除します。
- **クリーンアップ** — 無効/変更された項目、無効な pals および passives、無効な構造を削除します。不正な pals を修正 (合法的な最大値に制限)。対空砲塔をリセットします。 private chests のロックを解除します。すべての構造物を修復します。
- **リセット** — ミッション、ダンジョン、石油掘削装置、侵略者、補給物資をリセットします。
- **タイムスタンプ** — 負のタイムスタンプを修正します。プレイヤーの時間をリセットします。
- **PalDefender** — `killnearestbase` コマンドを生成します。





---




<div align="center">

## インストール

<img src="https://readme-typing-svg.demolab.com?lines=%E6%95%B0%E5%88%86%E3%81%A7%E3%81%99%E3%81%90%E3%81%AB%E5%AE%9F%E8%A1%8C%E5%8F%AF%E8%83%BD%3B%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89%E3%81%97%E3%81%A6%E3%81%8B%E3%82%89%E5%AE%9F%E8%A1%8C%3B%E3%81%84%E3%81%84%E3%81%88%2B%E3%82%BB%E3%83%83%E3%83%88%E3%82%A2%E3%83%83%E3%83%97%2B%E5%BF%85%E9%A0%88&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### スタンドアロン ビルド (推奨)

事前に構築されたバイナリは、[GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) 以降の 3 つの主要なプラットフォームすべてで利用できます。

|プラットフォーム |ダウンロード |要件 |
|----------|----------|--------------|
| **Windows** | `PalworldSaveTools-*.exe` | Windows 10/11、[VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022) |
| **Linux** | `PalworldSaveTools-*-linux` |最新のディストリビューション |
| **macOS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+ (モントレー以降) |

[Nexus Mods](https://www.nexusmods.com/palworld/mods/3190) でもご利用いただけます。

1. 使用しているプラ​​ットフォームに適切なビルドをダウンロードします。
2. 実行可能ファイルを抽出し (アーカイブされている場合)、実行します。
3. 以上です。Python や依存関係は必要ありません。

> **Windows:** 「VCRUNTIME140.dll が見つかりませんでした」と表示された場合は、[Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) をインストールしてください。

> **Linux:** ファイルを実行可能としてマークする必要がある場合があります: `chmod +x PalworldSaveTools-*-linux`

> **macOS:** Gatekeeper がアプリをブロックする場合は、最初に右クリック → **開く**、または `xattr -d com.apple.quarantine /path/to/app` を実行します。

### ソースから (すべてのプラットフォーム)

PST は依存関係の管理に [`uv`](https://docs.astral.sh/uv/) を使用します。起動スクリプトは自動的に仮想環境を作成し、すべてをインストールします。

**前提条件:** [Python 3.11+](https://www.python.org/) および [uv](https://docs.astral.sh/uv/getting-started/installation/)。

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows** (ダブルクリック ランチャー):
```
start.cmd
```

ランチャーは `.venv` を作成し、`uv sync` 経由で依存関係をインストールし、アプリを起動します。終了時にロックファイルがクリーンアップされるため、各実行が再現可能になります。





---




<div align="center">

## クイックスタート

<img src="https://readme-typing-svg.demolab.com?lines=%E8%AA%AD%E3%81%BF%E8%BE%BC%E3%81%BF%2B%E7%B7%A8%E9%9B%86%2B%E4%BF%9D%E5%AD%98%2B%E3%81%9D%E3%82%8C%E3%81%A0%E3%81%91%2B%E3%82%B7%E3%83%B3%E3%83%97%E3%83%AB%E3%80%82%3B3%2B%E3%82%B9%E3%83%86%E3%83%83%E3%83%97%2Bto%2B%E6%A0%84%E5%85%89%3B%E3%81%9D%E3%82%8C%E3%81%AF%2B%E3%81%9D%E3%82%8C%2B%E7%B0%A1%E5%8D%98%E3%81%A7%E3%81%99&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **セーブデータをロード**
   - **メニュー → ロード 保存** をクリックするか、`.sav` ファイルをウィンドウにドラッグ アンド ドロップします。
   - Palworld 保存フォルダーに移動し、`Level.sav` を選択します。

2. **データを探索する**
   - **マップ**、**ツール**、**プレイヤー**、**ギルド**、**拠点**、**プレイヤーインベントリ**、**ベースインベントリ**、**Pal Editor**、**除外**のタブを使用して、セーブデータを探索します。
   - 統計バーにはライブ数が表示されます。クイックナビアイコンは各セクションにジャンプします。

3. **変更を加える**
   - 左クリックして選択します。コンテキストに応じたアクションを実行するには、ほぼすべてのものを右クリックします。
   - ダブルクリックしてクイック編集またはクイック削除を行います (詳細についてはアプリ内ガイドを参照してください)。

4. **変更を保存**
   - [**メニュー → 変更を保存**] をクリックします。バックアップは自動的に作成されます。

> **ヒント:** 各タブにはガイドが組み込まれています。どのタブでもヘルプ アイコンをクリックすると、何ができるかを正確に確認できます。さらに詳しい知識が必要な場合は、**ボタン、フィールド、またはコントロールの上にカーソルを置く**と、ヘッダーに詳細なツールチップが表示されます。アプリ内のツールチップ ヘルプ システムは、各機能の機能とその使用方法を正確に理解するための最良のリファレンスです。





---




<div align="center">

## ガイド

<img src="https://readme-typing-svg.demolab.com?lines=%E3%82%B9%E3%83%86%E3%83%83%E3%83%97%E3%83%90%E3%82%A4%E3%82%B9%E3%83%86%E3%83%83%E3%83%97%2B%E3%82%A6%E3%82%A9%E3%83%BC%E3%82%AF%E3%82%B9%E3%83%AB%E3%83%BC%3B%2B%E3%82%AC%E3%82%A4%E3%83%89%E3%81%AB%E5%BE%93%E3%81%A3%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84%3B%E7%A7%81%E3%81%9F%E3%81%A1%E3%81%8C%2B%E3%81%8A%E8%A6%8B%E3%81%9B%E3%81%97%E3%81%BE%E3%81%99%2B%E3%81%9D%E3%81%AE%E6%96%B9%E6%B3%95&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### ファイルの保存場所

**ホスト / 協力プレイ (Windows):**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**専用サーバー:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### マップのロック解除

PST では、セーブ用にマップ全体 (すべてのファストトラベル ポイント) のロックを解除できます。

1. PST でセーブデータをロードします。
2. [**プレイヤー インベントリ**] タブを開き、単一プレイヤーの [**すべてのマップ + ファスト トラベルのロックを解除**] をクリックします。** または **
3. [ツール] タブの [**マップの復元**] ツールを使用して、**すべて**のワールド/サーバーにロック解除されたマップの進行状況を一度に適用します。
4. 変更を保存します。自動バックアップが作成されます。

### ホスト→サーバー転送

<details>
<summary>クリックして展開</summary>

1. `Level.sav` フォルダーと `Players` フォルダーをホストの保存場所からコピーします。
2. 専用サーバーの保存フォルダーに貼り付けます。
3. サーバーを起動し、新しいキャラクターを作成し、自動保存されるまで待ちます。
4. サーバーを閉じます。
5. PST で **ホスト保存の修正** を使用して、古いキャラクターの GUID を新しいものに移行します。
6. ファイルをコピーして戻し、サーバーを起動します。

</details>

### ホストスワップ (ホストの変更)

<details>
<summary>クリックして展開</summary>

**背景:** ホストは常に `0001.sav` スロットを使用します。これは、誰がホストしても同じ UID です。各クライアントは固有の通常の保存を取得します (`123xxx.sav` など)。

**前提条件:** 古いホストと新しいホストの両方に、キャラクターの参加と作成によって生成された通常のセーブが必要です。

**手順:**

1. **ホスト セーブの修正** を使用して、古いホストの `0001.sav` → 通常のセーブ (例: `123xxx.sav`) を交換します。これにより、進行状況がホスト スロットから移動されます。
2. **ホスト セーブの修正** を使用して、新しいホストの通常のセーブ (例: `987xxx.sav`) → `0001.sav` を交換します。これにより、進行状況がホスト スロットに移動されます。

**結果:** 新しいホストは、独自のキャラクターと Pals で `0001.sav` を占有します。古いホストは、元の進行状況がそのままの状態でクライアントになります。

</details>

### キャラクター転送(クロスセーブ)

<details>
<summary>クリックして展開</summary>

キャラクター、Pals、インベントリ、テクノロジーを維持しながら、異なるワールドまたはサーバー間でキャラクターを転送します。

1. [ツール] タブから **キャラクター転送** ツールを開きます。
2. ソース セーブとターゲット セーブを選択します。
3. 1 人のプレーヤーまたはすべてのプレーヤーを転送します。
4. 協力サーバーと専用サーバー間の移行に役立ちます。

</details>

### ベースのエクスポート/インポート/クローン

<details>
<summary>クリックして展開</summary>

**ベースのエクスポート:**
1. **Bases** タブに移動します (またはマップ ビューアーを使用します)。
2. ベースを右クリック → **ベースのエクスポート**。
3. `.json` ブループリント ファイルとして保存します。

**ベースのインポート:**
1. ターゲット ギルド ([拠点] タブ、[マップ ビューアー]、または [ギルド] タブ) を右クリックします。
2. **ベースのインポート** (単一ファイル) または **ベースのインポート (複数ファイル)** を選択します。
3. エクスポートした `.json` ファイルを選択します。

**ベースのクローン作成:**
1. ベースを右クリック→ [**ベースのクローン**] をクリックします。
2. 対象のギルドを選択します。
3. ベースはオフセット配置で複製されます。

**ベース半径の調整:**
1. ベースを右クリック → **半径の調整**。
2. 新しい半径 (50% ～ 1000%) を入力します。
3. 構造を再割り当てするには、ゲーム内で保存して再ロードします。

</details>





---




<div align="center">

## トラブルシューティング

<img src="https://readme-typing-svg.demolab.com?lines=%E3%81%84%E3%81%A4%2B%E7%89%A9%E4%BA%8B%2B%E8%A1%8C%E3%81%8F%2B%E6%A8%AA%E5%90%91%E3%81%8D%3B%E3%83%91%E3%83%8B%E3%83%83%E3%82%AF%E3%81%AB%E3%81%AA%E3%82%89%E3%81%AA%E3%81%84%E3%81%A7%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84%3B%E7%A7%81%E3%81%9F%E3%81%A1%E3%81%AF%2B%E8%A6%8B%E3%81%9F%2B%E3%81%9D%E3%82%8C%2B%E3%81%99%E3%81%B9%E3%81%A6&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 「VCRUNTIME140.dll が見つかりませんでした」(Windows)

[Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015 ～ 2022) をインストールします。

### `struct.error` 保存を解析するとき

保存ファイル形式が古いです。ゲーム内のセーブ (ソロ、協力、または専用サーバー) を一度ロードして、自動構造更新をトリガーしてから、再試行してください。最新のゲームパッチ以降にセーブデータが更新されていることを確認してください。

### GamePass コンバータが動作しない

1. Palworld の GamePass バージョンを完全に閉じます。
2. ファイル ハンドルが解放されるまで数分間待ちます。
3. GamePass → Steam コンバータを実行します。
4. GamePass で Palworld を起動して確認します。

### Linux / macOS バイナリが起動しない

- **Linux:** `chmod +x PalworldSaveTools-*-linux` を実行可能としてマークします。
- **macOS:** Gatekeeper によってブロックされている場合は、右クリック → **開く**、または `xattr -d com.apple.quarantine /path/to/app` を実行します。





---




<div align="center">

## ソースからのビルド

<img src="https://readme-typing-svg.demolab.com?lines=%E3%82%B3%E3%83%B3%E3%83%91%E3%82%A4%E3%83%AB%2B%E3%81%9D%E3%82%8C%2B%E8%87%AA%E5%88%86%E8%87%AA%E8%BA%AB%3B%2B%E3%81%82%E3%81%AA%E3%81%9F%E8%87%AA%E8%BA%AB%2B%E7%8B%AC%E8%87%AA%E3%81%AE%E3%82%82%E3%81%AE%E3%82%92%E6%A7%8B%E7%AF%89%3BFrom%2B%E3%82%BD%E3%83%BC%E3%82%B9%2Bto%2B%E3%83%90%E3%82%A4%E3%83%8A%E3%83%AA&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST は 2 つのビルド パスをサポートします。 CI/CD パイプラインは、クロスプラットフォーム リリース バイナリに Nuitka を使用します。 cx_Freeze は、ローカル Windows インストーラーに使用されます。

### Nuitka (クロスプラットフォーム — CI/リリースで使用)

Python 3.11+ および `uv` が必要です。 Nuitka は自動的にインストールされます。

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

出力は `dist/` に送られます。
- Windows → `dist/PalworldSaveTools-*.exe`
- Linux → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → `.dmg` としてパッケージ化

### cx_Freeze (Windows インストーラー)

ローカル Windows `.7z` パッケージの場合:

```
scripts\build_cx.cmd
```

これにより、プロジェクト ルートに `PST_standalone_v{version}.7z` が作成されます。

### インタラクティブビルダー

ビルドモードを選択するための対話型メニュー:

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## 貢献する

<img src="https://readme-typing-svg.demolab.com?lines=%E5%8A%A9%E3%81%91%E3%81%9F%E3%81%84%2B%E3%81%97%E3%81%9F%E3%81%84%3F%2B%E6%96%B9%E6%B3%95%E3%81%AF%E3%81%93%E3%81%A1%E3%82%89%3B%E3%83%81%E3%83%BC%E3%83%A0%E3%81%AB%E5%8F%82%E5%8A%A0%E3%81%99%E3%82%8B%3B%E3%81%99%E3%81%B9%E3%81%A6%20%2B%20%E8%B2%A2%E7%8C%AE%20%2B%20%E3%82%AB%E3%82%A6%E3%83%B3%E3%83%88&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

貢献は大歓迎です!お気軽にプルリクエストを送信してください。

1. リポジトリをフォークします。
2. 機能ブランチ (`git checkout -b feature/AmazingFeature`) を作成します。
3. 変更をコミットします (`git commit -m 'Add some AmazingFeature'`)。
4. ブランチ (`git push origin feature/AmazingFeature`) にプッシュします。
5. プルリクエストを開きます。





---




<div align="center">

## 免責事項

<img src="https://readme-typing-svg.demolab.com?lines=%E8%AA%AD%E3%82%93%E3%81%A7%2B%E3%81%93%E3%82%8C%2B%E5%89%8D%2B%E3%81%82%E3%81%AA%E3%81%9F%2B%E4%BC%91%E6%86%A9%2B%E4%BD%95%E3%81%8B%3B%E3%81%82%E3%81%AA%E3%81%9F%E3%81%AF%2B%E8%AD%A6%E5%91%8A%E3%81%95%E3%82%8C%E3%81%BE%E3%81%97%E3%81%9F%2B%3B%E3%83%90%E3%83%83%E3%82%AF%E3%82%A2%E3%83%83%E3%83%97%2B%E3%83%95%E3%82%A1%E3%83%BC%E3%82%B9%E3%83%88%21%3B%2B%E5%81%89%E5%A4%A7%E3%81%AA%2B%E5%8A%9B%E3%81%A7...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>
**このツールはご自身の責任で使用してください。変更を加える前に、必ず保存ファイルをバックアップしてください。**

開発者は、このツールの使用によって発生する可能性のあるセーブデータの損失や問題について責任を負いません。





---




<div align="center">

## サポート

<img src="https://readme-typing-svg.demolab.com?lines=%E7%A7%81%E3%81%9F%E3%81%A1%E3%81%AF%E3%81%82%E3%81%AA%E3%81%9F%E3%81%AE%2B%E3%82%92%2B%E6%8C%81%E3%81%A3%E3%81%A6%E3%81%84%E3%81%BE%E3%81%99%2B%3B%2B%E5%8A%A9%E3%81%91%E3%81%8C%E5%BF%85%E8%A6%81%E3%81%A7%E3%81%99%E3%81%8B%3F%3B%E7%A7%81%E3%81%9F%E3%81%A1%E3%81%AF%2B%E3%81%93%E3%81%93%E3%81%AB%2B%E3%81%82%E3%81%AA%E3%81%9F%E3%81%AE%E3%81%9F%E3%82%81%E3%81%AB%2B%E3%81%84%E3%81%BE%E3%81%99&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub 問題:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Nexus Mods:** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## ライセンス

<img src="https://readme-typing-svg.demolab.com?lines=MIT%2B%E2%80%94%2Bdo%2Bwhatever%2Byou%2Bwant%3B%E7%84%A1%E6%96%99%2B%E3%81%9D%E3%81%AE%E3%81%BE%E3%81%BE%2B%E4%B8%AD%2B%E3%83%93%E3%83%BC%E3%83%AB%3B%E3%82%AA%E3%83%BC%E3%83%97%E3%83%B3%2B%E3%82%BD%E3%83%BC%E3%82%B9%E3%80%81%2B%E3%82%AA%E3%83%BC%E3%83%97%E3%83%B3%2B%E3%83%9E%E3%82%A4%E3%83%B3%E3%83%89&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

このプロジェクトは MIT ライセンスに基づいてライセンスされています。詳細については、[license](license) ファイルを参照してください。





---




<div align="center">

## パルワールドチーム

<img src="https://readme-typing-svg.demolab.com?lines=%E3%82%B6%2B%E4%BA%BA%E3%80%85%2B%E8%83%8C%E5%BE%8C%2B%E3%82%B6%2B%E9%AD%94%E6%B3%95%3B%2B%E3%83%81%E3%83%BC%E3%83%A0%E3%81%AB%E4%BC%9A%E3%81%86%3B%2B%E6%83%85%E7%86%B1%E3%82%92%E6%8C%81%E3%81%A3%E3%81%A6%E6%A7%8B%E7%AF%89%E3%81%95%E3%82%8C%E3%81%9F&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

このプロジェクトは、背後にいる人々なしでは存在しません。

**[Pylar](https://github.com/deafdudecomputers)** — すべてを始めた男。このツールのすべての行は、彼のビジョンと、保存エンジン、GUI、および毎日使用する機能に対するたゆまぬ努力をたどります。

**[cyrix](https://github.com/CyrixJD115)** — リファクタラーおよびサブメンテナ。コードの品質、簡素化、構造の改善に重点を置き、プロジェクトの成長に合わせてコードベースをクリーンで小さく、保守しやすく保ちます。

**[dkoz](https://github.com/dkoz)** — ID の背後にいる男。ゲーム データ ID、ID コードの構造的洞察、およびゲームの更新ごとにツールの正確性を維持する Palworld のデータがどのように連携されているかに関する深い知識を提供します。

**[oMaN-Rod](https://github.com/oMaN-Rod)** — このプロジェクトのフォーク元となったオリジナルの保存パーサーを提供しました。 Palworld 保存形式のクラックに関する彼の基礎的な作業がなければ、これは存在しませんでした。フォークにより、彼のパーサーは合理化され、簡素化され、現在の PST になりました。


**[Okaetsu](https://github.com/Okaetsu)** — Base import/export would not have been possible without their modding insights.




---




<div align="center">

## 謝辞

<img src="https://readme-typing-svg.demolab.com?lines=%2B%E3%82%AF%E3%83%AC%E3%82%B8%E3%83%83%E3%83%88%2B%E3%81%AE%2B%E6%9C%9F%E9%99%90%E3%81%AF%E3%81%A9%E3%81%93%E3%81%A7%E3%81%99%E3%81%8B%3B%E3%81%82%E3%82%8A%E3%81%8C%E3%81%A8%E3%81%86%2B%E3%81%82%E3%82%8A%E3%81%8C%E3%81%A8%E3%81%86%2B%E3%81%BF%E3%82%93%E3%81%AA%3B%E7%A7%81%E3%81%9F%E3%81%A1%2B%E7%AB%8B%E3%81%A4%2B%E8%82%A9%E3%81%AE%E4%B8%8A%E3%81%AB%E7%AB%8B%E3%81%A4&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

以下の方々に多大な感謝を申し上げます:

- **Palworld** は Pocketpair, Inc. によって開発され、私たち全員を一つにまとめたゲームです。
- **バグ報告者** — 提出されたすべての問題、見つかったすべてのエッジケース、Discord に貼り付けられたすべてのログ。レポートごとにこのツールをより堅牢にします。
- **Palworld モッディング コミュニティ** — 知識を共有し、フォーマットをリバース エンジニアリングし、エコシステムを前進させるモッダー仲間、ツール開発者、改造者です。このプロジェクトは、その共同の努力の上に成り立っています。
- **すべての寄稿者およびコミュニティ メンバー** — PR を送信したことがある方、Discord の質問に回答したことがある方、単に PST について友人に話したことがあることにかかわらず – ありがとうございます。

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**Palworld コミュニティのために ❤️ で作成されました**

[⬆ Back to Top](#palworld-save-tools)

</div>