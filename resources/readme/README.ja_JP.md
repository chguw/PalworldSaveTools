<div align="center">

![PalworldSaveTools Logo](../PalworldSaveTools_Blue.png)

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

## 目次

- [特徴](#特徴)
- [インストール](#インストール)
- [クイックスタート](#クイックスタート)
- [ツールの概要](#ツールの概要)
- [ガイド](#ガイド)
- [トラブルシューティング](#トラブルシューティング)
- [スタンドアロン実行可能ファイルのビルド (Windows のみ)](#スタンドアロン実行可能ファイルのビルド-windows-のみ)
- [貢献する](#貢献する)
- [ライセンス](#ライセンス)

---

## 特徴

### コア機能

|特集 |説明 |
|----------|---------------|
| **高速保存解析** |利用可能な保存ファイル リーダーの中で最も速いものの 1 つ |
| **プレイヤー管理** |表示、編集、名前変更、レベル変更、テクノロジーのロック解除、プレーヤーの管理 |
| **ギルド管理** |プレイヤーの作成、名前変更、移動、ラボ研究のロック解除、ギルドの管理 |
| **Pal Editor** |ステータス、スキル、IVs、ランク、ソウル、性別、ボス/ラッキー切り替え用の完全なエディター |
| **ベースキャンプツール** |エクスポート、インポート、クローン作成、半径の調整、およびベースの管理 |
| **マップビューア** |座標と詳細を含むインタラクティブなベースとプレーヤーのマップ |
| **キャラクター転送** |異なるワールド/サーバー間でキャラクターを転送する (クロスセーブ) |
| **変換を保存** | Steam 形式と GamePass 形式の間で変換する |
| **ワールド設定** | WorldOption と LevelMeta 設定を編集する |
| **タイムスタンプ ツール** |負のタイムスタンプを修正し、プレーヤーの時間をリセットする |

### オールインワン ツール

**オールインワン ツール** スイートは、包括的な保存管理を提供します。

- **削除ツール**
  - プレイヤー、拠点、またはギルドを削除する
  - 時間のしきい値に基づいて非アクティブなプレーヤーを削除します
  - 重複したプレイヤーと空のギルドを削除します
  - 参照されていない/孤立したデータを削除する

- **クリーンアップ ツール**
  - 無効な/変更されたアイテムを削除します
  - 無効な pals および passives を削除します
  - 不正な pals を修正 (合法的な最大統計に制限)
  - 無効な構造を削除する
  - 対空砲塔をリセット
  - private chestsのロックを解除する

- **ギルドツール**
  - すべてのギルドを再構築する
  - ギルド間でプレイヤーを移動する
  - プレイヤーのギルドリーダーを作る
  - ギルド名の変更
  - 最大ギルドレベル
  - すべての研究室の研究をアンロック

- **プレーヤーツール**
  - プレーヤー pal の統計とスキルを編集
  - すべてのテクノロジーのロックを解除する
  - 観察ケージのロックを解除する
  - プレイヤーのレベルアップ/レベルダウン
  - プレイヤーの名前を変更する

- **ユーティリティの保存**
  - ミッションをリセット
  - ダンジョンのリセット
  - タイムスタンプを修正
  - 過剰な在庫を削減する
  - PalDefender コマンドを生成する

### 追加ツール

|ツール |説明 |
|------|---------------|
| **プレーヤー Pals** を編集 |ステータス、スキル、IVs、才能、魂、ランク、性別を含む完全な pal editor |
| **SteamIDコンバータ** | Steam ID を Palworld UID に変換する |
| **ホストの保存を修正** | 2 人のプレーヤー間で UID を交換します (ホスト交換など)。
| **スロット インジェクター** |プレイヤーごとの Palbox スロットを増やす |
| **マップを復元** |ロック解除されたマップの進行状況をすべてのワールド/サーバーに適用 |
| **ワールドの名前を変更** | LevelMeta でワールド名を変更する |
| **WorldOption エディター** |ワールドの設定と構成を編集する |
| **レベルメタエディタ** |ワールドのメタデータ (名前、ホスト、レベル) を編集 |

---

## インストール

### 前提条件

**スタンドアロン (Windows) の場合:**
- Windows 10/11
- [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version) (2015-2022)

**ソースから実行する場合 (すべてのプラットフォーム):**
- Python 3.11以降

### スタンドアロン (Windows - 推奨)

1. [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) から最新リリースをダウンロードします。
2.zipファイルを解凍します。
3. `PalworldSaveTools.exe` を実行します。

### ソースから (すべてのプラットフォーム)

起動スクリプトは自動的に仮想環境を作成し、すべての依存関係をインストールします。

**uv の使用:**
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

### 支店

- **安定** (推奨): `git clone https://github.com/deafdudecomputers/PalworldSaveTools.git`
- **ベータ** (最新機能): `git clone -b beta https://github.com/deafdudecomputers/PalworldSaveTools.git`

---

## クイックスタート

1. **セーブデータをロード**
   - ヘッダーのメニューボタンをクリックします
   - **読み込み保存**を選択します
   - Palworld 保存フォルダーに移動します
   - `Level.sav` を選択します

2. **データを探索する**
   - タブを使用してプレーヤー、ギルド、基地、またはマップを表示します
   - 特定のエントリを見つけるための検索とフィルタリング

3. **変更を加える**
   - 編集、削除、または変更する項目を選択します
   - 右クリックすると、追加オプションを含むコンテキスト メニューが表示されます

4. **変更を保存**
   - メニュー ボタン → **変更を保存** をクリックします。
   - バックアップは自動的に作成されます

---

## ツールの概要

### オールインワン ツール (AIO)

包括的な保存管理のためのメイン インターフェイスには 5 つのタブがあります。

**プレーヤー インベントリ タブ** - サーバー上のすべてのプレーヤーのインベントリを表示および管理します
- プレイヤーの統計、インベントリ、装備されているギアを編集します。
- 品質を編集し、インベントリや装備されているギアから何かを追加、削除する機能。

**「拠点在庫」タブ** - サーバー上のすべての拠点の在庫を表示および管理します。
- 基本在庫を編集します。
- コンテナのクリア、品質の編集、ベースインベントリへの追加や削除が可能。
- 不正行為の可能性を考慮したフィルタリングが含まれています。

**「プレイヤー」タブ** - サーバー上のすべてのプレイヤーを表示および管理します
- プレイヤー名、レベル、pal カウントを編集
- 非アクティブなプレイヤーを削除する
- プレイヤーのギルドと前回のオンライン時間を表示します

**ギルド タブ** - ギルドとその拠点を管理します
- ギルドの名前を変更し、リーダーを変更します
- 拠点の場所とレベルを表示
- 空のギルドまたは非アクティブなギルドを削除します

**「ベース」タブ** - すべてのベースキャンプを表示
- ベースブループリントのエクスポート/インポート
- 他のギルドに基地のクローンを作成
- ベースの半径を調整する

### マップビューア

あなたの世界をインタラクティブに視覚化:
- すべての基地の場所とプレーヤーの位置を表示
- ギルド名またはプレイヤー名でフィルタリングします
- マーカーをクリックすると詳細情報が表示されます
- PalDefender の `killnearestbase` コマンドを生成します

### キャラクター転送

異なるワールド/サーバー間でキャラクターを転送する (クロスセーブ):
- 一人または全員のプレイヤーを転送します
- キャラクター、pals、インベントリ、テクノロジーを保存します
- 協力サーバーと専用サーバー間の移行に役立ちます

### ホスト保存を修正

2 人のプレイヤー間で UID を交換します。
- 進行状況をあるプレイヤーから別のプレイヤーに転送する
- ホスト/協力プレイからサーバーへの転送に必須
- プレイヤー間でホストの役割を交換するのに役立ちます
- プラットフォームの交換に便利 (Xbox ↔ Steam)
- ホスト/サーバーの UID 割り当ての問題を解決します。
- **注意:** 影響を受けるプレイヤーは、最初にターゲットセーブでキャラクターを作成する必要があります。

---

## ガイド

### ファイルの保存場所

**ホスト/協力:**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**専用サーバー:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### マップのロック解除

<details>
<summary>クリックしてマップのロック解除手順を展開</summary>

1. `resources\` から `LocalData.sav` をコピーします
2.サーバー/ワールド保存フォルダーを見つけます
3. 既存の `LocalData.sav` をコピーしたファイルで置き換えます
4. 完全にロックが解除されたマップでゲームを起動します

> **注:** [ツール] タブの [**マップの復元**] ツールを使用すると、ロック解除されたマップが自動バックアップですべてのワールド/サーバーに一度に適用されます。

</details>

### ホスト→サーバー転送

<details>
<summary>クリックしてホストからサーバーへの転送ガイドを展開</summary>

1. `Level.sav` および `Players` フォルダーをホストの保存場所からコピーします。
2. 専用サーバーの保存フォルダーに貼り付けます
3.サーバーを起動し、新しいキャラクターを作成します
4. 自動保存されるまで待ってから閉じます
5. **ホスト保存の修正**を使用して GUID を移行します
6. ファイルをコピーして戻して起動します

**修正ホスト保存の使用:**
- 一時フォルダーから `Level.sav` を選択します
- **古いキャラクター** (元のセーブから) を選択します
- **新しいキャラクター** (先ほど作成したもの) を選択します
- [**移行**] をクリックします。

</details>

### ホストスワップ (ホストの変更)

<details>
<summary>クリックしてホスト スワップ ガイドを展開</summary>

**背景:**
- ホストは常に `0001.sav` を使用します - 誰がホストしても同じ UID
- 各クライアントは固有の通常の UID 保存を使用します (例: `123xxx.sav`、`987xxx.sav`)。

**前提条件:**
両方のプレーヤー (古いホストと新しいホスト) が通常のセーブを生成する必要があります。これは、ホストの世界に参加し、新しいキャラクターを作成することで発生します。

**手順:**

1. **定期的な保存が存在することを確認します**
   - プレーヤー A (古いホスト) には通常のセーブ (例: `123xxx.sav`) が必要です。
   - プレーヤー B (新しいホスト) には通常のセーブが必要です (例: `987xxx.sav`)

2. **古いホストのホスト セーブを通常のセーブに交換**
   - PalworldSaveTools **ホスト保存を修正** を使用して交換します。
   - 古いホストの `0001.sav` → `123xxx.sav`
   - (これにより、古いホストの進行状況がホスト スロットから通常のプレイヤー スロットに移動します)

3. **新しいホストの通常の保存をホストの保存に交換**
   - PalworldSaveTools **ホスト保存を修正** を使用して交換します。
   - 新しいホストの `987xxx.sav` → `0001.sav`
   - (これにより、新しいホストの進行状況がホスト スロットに移動されます)

**結果:**
- プレイヤー B は、独自のキャラクターと `0001.sav` の pals を持つホストになりました。
- プレーヤー A は、`123xxx.sav` の元の進行状況でクライアントになります。

</details>

### 基本エクスポート/インポート

<details>
<summary>クリックして基本エクスポート/インポート ガイドを展開</summary>

**ベースのエクスポート:**
1. PST でセーブデータをロードします
2.「拠点」タブに移動します
3. ベースを右クリック → ベースのエクスポート
4. `.json` ファイルとして保存します

**ベースのインポート:**
1. 「Bases」タブまたは「Base Map Viewer」に移動します。
2. 拠点をインポートしたいギルドを右クリックします。
3. インポートベースを選択します
4. エクスポートした `.json` ファイルを選択します

**ベースのクローン作成:**
1. ベースを右クリック→「ベースのクローン」
2.対象ギルドを選択
3. ベースはオフセット配置で複製されます。

**ベース半径の調整:**
1. ベースを右クリック → 半径を調整
2. 新しい半径を入力します (50% ～ 1000%)
3. 再割り当てする構造物をゲーム内で保存してロードします。

</details>

---

## トラブルシューティング

### 「VCRUNTIME140.dll が見つかりませんでした」

**解決策:** [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version) をインストールします

### `struct.error` 保存解析時

**原因:** 保存ファイル形式が古いです

**解決策:**
1. ゲームにセーブデータをロードします (ソロ、コープ、または専用サーバー モード)
2. これにより、構造の自動更新がトリガーされます
3. セーブデータが最新のゲームパッチ以降に更新されていることを確認します。

### GamePass コンバータが動作しない

**解決策:**
1. Palworld の GamePass バージョンを閉じます
2. 数分待ちます
3. Steam → GamePass コンバータを実行します。
4. GamePass で Palworld を起動して確認します

---

## スタンドアロン実行可能ファイルのビルド (Windows のみ)

ビルド スクリプトを実行して、スタンドアロンの実行可能ファイルを作成します。

```bash
scripts\build.cmd
```

これにより、プロジェクト ルートに `PST_standalone_v{version}.7z` が作成されます。

---

## 貢献する

貢献は大歓迎です！お気軽にプルリクエストを送信してください。

1. リポジトリをフォークする
2. 機能ブランチを作成します (`git checkout -b feature/AmazingFeature`)
3. 変更をコミットします (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュします (`git push origin feature/AmazingFeature`)
5. プルリクエストを開く

---

## 免責事項

**このツールはご自身の責任で使用してください。変更を加える前に、必ず保存ファイルをバックアップしてください。**

開発者は、このツールの使用によって発生する可能性のあるセーブデータの損失や問題について責任を負いません。

---

## サポート

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub 問題:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **ドキュメント:** [Wiki](https://github.com/deafdudecomputers/PalworldSaveTools/wiki) *(現在開発中)*

---

## ライセンス

このプロジェクトは MIT ライセンスに基づいてライセンスされています。詳細については、[LICENSE](LICENSE) ファイルを参照してください。

---

## 謝辞

- **Palworld** は Pocketpair, Inc. によって開発されました。
- このツールの改善に協力してくれたすべての貢献者とコミュニティ メンバーに感謝します

---

<div align="center">

**Palworld コミュニティのために ❤️ で作成されました**

[⬆ Back to Top](#palworldsavetools)

</div>