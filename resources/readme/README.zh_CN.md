<div align="center">

![PalworldSaveTools Logo](../PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Palworld 的综合保存文件编辑工具包**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

---

### **从 [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** 下载独立版本

---

</div>
<div align="center">

## 概述

<img src="https://readme-typing-svg.demolab.com?lines=What+exactly+is+this+thing%3F;Your+save%2C+your+way;One+tool+to+rule+them+all&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) 是一款快速、一体化的桌面应用程序，用于检查和编辑 Palworld 保存文件。它使用 Python 和 PySide6 构建，可以直接读取和写入游戏的压缩保存格式 - 无需游戏模组。

无论您需要管理专用服务器、在合作服务器和专用服务器之间迁移、清理废弃的数据还是微调单个 Pals，PST 都为所有这些提供了一个统一的界面。

### 亮点

- **跨平台** — 适用于 **Windows**、**Linux** 和 **macOS** 的预构建二进制文件。
- **快速本机解析** — 最快的保存文件读取器之一，由 [`palsav`](src/palsav) 引擎提供支持。
- **视觉地图** - 带有基地/玩家标记、禁区和坐标校准的交互式世界地图。
- **深度 Pal 编辑** — 完全控制统计数据、IVs、灵魂、技能、passives、工作适宜性、等级和外观标志。
- **服务器级工具** — 为管理员构建的批量删除、清理、转换和字符传输。
- **自动备份** — 每个保存操作都会在写入之前创建备份。
- **8 种语言** — 本地化 UI、应用内指南和文档。





---





## 目录

- [概述](#概述)
- [特点](#特点)
- [安装](#安装)
- [快速入门](#快速入门)
- [指南](#指南)
- [故障排除](#故障排除)
- [从源代码构建](#从源代码构建)
- [贡献](#贡献)
- [许可证](#许可证)
- [Palworld 团队](#palworld-团队)

- [支持](#support)
- [许可证](#license)
- [致谢](#致谢)





---




<div align="center">

## 特点

<img src="https://readme-typing-svg.demolab.com?lines=The+good+stuff;Check+it+out;Packed+with+tools&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 玩家管理

- 按姓名、等级、pal 计数、UID、公会和最后上线时间查看和搜索所有玩家。
- 编辑玩家姓名、等级、统计数据和技术点。
- **跨多个玩家的批量操作**：物品管理、pal 管理和技术解锁。
- 按时间阈值删除不活跃玩家；删除重复项。

### Pal Editor

适用于任何玩家拥有的任何 Pal 的深度编辑界面。 Pals 由 **Party**（现役小队）和 **Palbox**（存储）组织。

- **统计数据和 IVs** — 生命值、攻击力、防御力 (IV 0–100)、等级 (1–80)、信任等级 (0–10)。
- **灵魂** — 生命值、攻击力、防御力、工艺速度 (0–20)。
- **技能** — 主动技能选择器；学习所有动作； Pals 的批量同步技能。
- **被动特征** — 具有完整游戏数据的被动选择器。
- **工作适宜性** — 设置个人工作适宜性级别 (0–10)。
- **外观标志** — 切换 Boss/Alpha、Lucky/Shiny、觉醒和导入/DNA。
- **排名和锁定** — 设置排名和最喜爱的锁定级别 (0–3)。
- 添加新的 Pals 或双击快速删除。

### 公会管理

两面板视图：顶部是公会列表，下面是成员名册。

- 重命名公会，更换领导者，设置公会等级，最高公会等级。
- 解锁所有实验室研究；重建所有公会。
- 在公会之间移动玩家；删除空的或不活跃的公会。

### 大本营工具

- 查看所有有公会协会的大本营。
- **导出**基础蓝图到`.json`； **导入**（单个或多个文件）到任何公会。
- **克隆**基地到其他具有偏移定位的公会。
- **调整基础半径** (50%–1000%)。
- 删除不活动的基地和非基地地图对象。

### 地图查看器

整个世界的交互式可视化。

- 带有详细面板的基地标记（房屋图标）和玩家标记（人物图标）。
- 切换覆盖：基地、球员、半径环、禁区。
- **区域绘制** — 直接在地图上绘制矩形或多边形禁区。
- **校准模式** — 将地图与游戏坐标精确对齐。
- 世界地图和树状地图视图；按公会或玩家名称过滤。
- 缩放 (1.0x–30.0x)、平移、双击以飞至标记。
- 右键单击​​标记和空白区域以进行管理操作。

### 库存管理

**玩家清单** — 三个子选项卡：
- *库存* — 主包中的所有物品和设备；编辑数量、添加、删除。
- *关键物品* — 任务物品、雕像和技术；批量添加所有肖像/关键物品。
- *统计数据* — 等级、生命值、耐力、攻击力、防御力、工作速度、重量。
- 武器、配件、食物、盔甲、盾牌、滑翔机和模块插槽的设备面板。
- 一键解锁所有地图+快速旅行点。

**基地库存** — 浏览和管理所有基地的物品和工作 Pals：
- 查看/编辑容器中的项目；透明容器；修改容器槽位。
- 跨公会物品操作（查找/删除所有公会的物品）。
- 跨行会结构删除。
- **基地 Pals** 子选项卡 — 使用完整的 pal 编辑器上下文菜单管理分配给每个基地的工作 Pals。

### 排除情况

保护名单，保护玩家、公会和基地免受清理行动的影响。

- 三个并排面板：排除的玩家 UID、公会 ID 和基本 ID。
- 通过右键单击“玩家”、“公会”或“基地”选项卡中的上下文菜单添加条目。
- 持久保存和加载排除列表。
- **在**运行批量清理之前**构建您的列表。

### 保存工具

可从 **工具** 选项卡作为可点击的卡片进行访问：

|工具|描述 |
|------|-------------|
| **转换保存** | SAV 和 JSON 格式之间的转换 |
| **转换 GamePass → Steam** |将 Xbox/GamePass 保存转换为 Steam 格式 |
| **转换 SteamID** |将 Steam ID 转换为 Palworld UID |
| **恢复地图** |将完全解锁的地图进度应用于所有世界/服务器 |
| **槽式注入器** |增加每位玩家的 palbox 槽位 |
| **修改保存** |打开并修改原始保存数据|
| **角色转移** |在不同世界/服务器之间转移角色（交叉保存）|
| **修复主机保存** |在两个玩家之间交换 UID（主机交换、平台迁移）|

### 清理和实用函数

这些服务器级操作可通过**菜单 → 功能**进行访问，包括：

- **删除** — 删除空公会、不活跃的基地/玩家、重复的玩家、未引用的数据。
- **清理** — 删除无效/修改的项目、无效的 pals 和 passives、无效的结构；修复非法的 pals （上限为合法最大值）；重置防空炮塔；解锁private chests；修复所有结构。
- **重置** — 重置任务、地下城、石油钻井平台、入侵者、空投补给。
- **时间戳** — 修复负时间戳；重置玩家时间。
- **PalDefender** — 生成 `killnearestbase` 命令。





---




<div align="center">

## 安装

<img src="https://readme-typing-svg.demolab.com?lines=Get+it+running+in+minutes;Download+and+go;No+setup+required&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 独立构建（推荐）

预构建的二进制文件适用于 [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) 的所有三个主要平台：

|平台|下载 |要求|
|----------|----------|--------------|
| **Windows** | `PalworldSaveTools-*.exe` | Windows 10/11，[VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022) |
| **Linux** | `PalworldSaveTools-*-linux` |任何现代发行版 |
| **macOS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+（蒙特利或更高版本）|

也可在 [Nexus Mods](https://www.nexusmods.com/palworld/mods/3190) 上找到。

1. 下载适合您平台的版本。
2. 解压（如果已存档）并运行可执行文件。
3. 就是这样——不需要 Python 或依赖项。

> **Windows：** 如果您看到“未找到 VCRUNTIME140.dll”，请安装 [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)。

> **Linux:** 您可能需要将文件标记为可执行文件：`chmod +x PalworldSaveTools-*-linux`

> **macOS：** 如果 Gatekeeper 阻止该应用程序，请首次右键单击 → **打开**，或运行 `xattr -d com.apple.quarantine /path/to/app`。

### 来自源头（所有平台）

PST 使用 [`uv`](https://docs.astral.sh/uv/) 进行依赖性管理。启动脚本会自动创建虚拟环境并安装所有内容。

**先决条件：** [Python 3.11+](https://www.python.org/) 和 [uv](https://docs.astral.sh/uv/getting-started/installation/)。

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows**（双击启动器）：
```
start.cmd
```

启动器创建 `.venv`，通过 `uv sync` 安装依赖项，然后启动应用程序。它会在退出时清除锁定文件，因此每次运行都是可重现的。





---




<div align="center">

## 快速入门

<img src="https://readme-typing-svg.demolab.com?lines=Load.+Edit.+Save.+That+simple.;Three+steps+to+glory;It%27s+that+easy&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **加载您的保存**
   - 单击 **菜单 → 加载保存**，或将 `.sav` 文件拖放到窗口上。
   - 导航到您的 Palworld 保存文件夹并选择 `Level.sav`。

2. **探索您的数据**
   - 使用选项卡 - **地图**、**工具**、**玩家**、**公会**、**基地**、**玩家库存**、**基地库存**、**Pal Editor**、**排除** - 探索您的保存。
   - 统计栏显示实时计数；快速导航图标跳转到每个部分。

3. **做出改变**
   - 左键单击选择；右键单击几乎任何内容即可执行上下文操作。
   - 双击可快速编辑或快速删除（详情请参阅应用内指南）。

4. **保存您的更改**
   - 单击**菜单 → 保存更改**。备份是自动创建的。

> **提示：** 每个选项卡都有一个内置指南 - 单击任何选项卡中的帮助图标即可准确查看其功能。如需更深入的了解，**将鼠标悬停在任何按钮、字段或控件上**即可在标题处显示详细的工具提示。应用程序内工具提示帮助系统是您准确了解每个功能的用途以及如何使用它的最佳参考。





---




<div align="center">

## 指南

<img src="https://readme-typing-svg.demolab.com?lines=Step-by-step+walkthroughs;Follow+the+guide;We%27ll+show+you+how&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 保存文件位置

**主机/合作社 (Windows)：**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**专用服务器：**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### 地图解锁

PST 可以解锁完整地图（所有快速旅行点）以供您保存：

1. 将您的保存加载到 PST 中。
2. 打开**玩家清单**选项卡，然后单击单个玩家的**解锁全地图+快速旅行**，**或**
3. 使用“工具”选项卡中的“恢复地图”工具一次性将解锁的地图进度应用到“所有”世界/服务器。
4. 保存更改。创建自动备份。

### 主机→服务器传输

<details>
<summary>点击展开</summary>

1. 从主机保存中复制 `Level.sav` 和 `Players` 文件夹。
2. 将它们粘贴到专用服务器保存文件夹中。
3. 启动服务器，创建新角色，等待自动保存。
4. 关闭服务器。
5. 使用 PST 中的 **修复主机保存** 将旧角色的 GUID 迁移到新角色。
6. 将文件复制回来并启动服务器。

</details>

### 主机交换（更改主机）

<details>
<summary>点击展开</summary>

**背景：** 主机始终使用 `0001.sav` 插槽 - 无论主机是谁，都使用相同的 UID。每个客户端都会获得唯一的定期保存（例如 `123xxx.sav`）。

**前提：** 新旧宿主都必须有加入和创建角色所生成的常规存档。

**步骤：**

1. 使用 **Fix Host Save** 将旧主机的 `0001.sav` → 其常规保存（例如 `123xxx.sav`）交换。这会将他们的进度移出主机槽。
2. 使用 **Fix Host Save** 交换新主机的常规保存（例如 `987xxx.sav`） → `0001.sav`。这会将他们的进度移至主机槽中。

**结果：** 新宿主现在以自己的角色和Pals占据`0001.sav`；旧主机成为客户端，原始进度完好无损。

</details>

### 角色传输（交叉保存）

<details>
<summary>点击展开</summary>

在不同世界或服务器之间转移角色，同时保留角色、Pals、库存和技术：

1. 从“工具”选项卡打开“**字符传输**”工具。
2. 选择源保存和目标保存。
3. 转移单个玩家或所有玩家。
4. 对于在合作服务器和专用服务器之间迁移很有用。

</details>

### 基础导出/导入/克隆

<details>
<summary>点击展开</summary>

**导出基地：**
1. 转到 **Bases** 选项卡（或使用地图查看器）。
2. 右键单击​​基地 → **导出基地**。
3. 另存为 `.json` 蓝图文件。

**导入基础：**
1. 右键单击目标公会（在“基地”选项卡、地图查看器或“公会”选项卡中）。
2. 选择**导入库**（单个文件）或**导入库（多文件）**。
3. 选择导出的 `.json` 文件。

**克隆基地：**
1. 右键单击一个碱基 → **克隆碱基**。
2. 选择目标公会。
3. 底座采用偏移定位克隆。

**调整基础半径：**
1. 右键单击底座 → **调整半径**。
2. 输入新的半径 (50%–1000%)。
3. 保存并重新加载游戏中的保存内容以重新分配结构。

</details>





---




<div align="center">

## 故障排除

<img src="https://readme-typing-svg.demolab.com?lines=When+things+go+sideways;Don%27t+panic;We%27ve+seen+it+all&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### “未找到 VCRUNTIME140.dll”(Windows)

安装 [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022)。

### 解析保存时的 `struct.error`

保存文件格式已过时。在游戏中加载保存（单人、合作或专用服务器）一次以触发自动结构更新，然后重试。确保在最新游戏补丁时或之后更新了保存。

### GamePass 转换器不工作

1.完全关闭GamePass版本的Palworld。
2. 等待几分钟，让文件句柄释放。
3. 运行GamePass → Steam 转换器。
4. 在GamePass上启动Palworld进行验证。

### Linux / macOS 二进制文件无法启动

- **Linux:** `chmod +x PalworldSaveTools-*-linux` 将其标记为可执行。
- **macOS：** 如果被 Gatekeeper 阻止，请右键单击 → **打开**，或运行 `xattr -d com.apple.quarantine /path/to/app`。





---




<div align="center">

## 从源代码构建

<img src="https://readme-typing-svg.demolab.com?lines=Compile+it+yourself;Build+your+own;From+source+to+binary&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST 支持两种构建路径。 CI/CD 管道使用 Nuitka 来跨平台发布二进制文件； cx_Freeze 用于本地 Windows 安装程序。

### Nuitka（跨平台 — 由 CI/版本使用）

需要 Python 3.11+ 和 `uv`。 Nuitka 会自动安装。

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

输出转到 `dist/`：
- Windows → `dist/PalworldSaveTools-*.exe`
- Linux → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → 打包为 `.dmg`

### cx_Freeze（Windows 安装程序）

对于本地 Windows `.7z` 包：

```
scripts\build_cx.cmd
```

这将在项目根目录中创建 `PST_standalone_v{version}.7z` 。

### 交互式生成器

用于选择构建模式的交互式菜单：

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## 贡献

<img src="https://readme-typing-svg.demolab.com?lines=Want+to+help%3F+Here%27s+how;Join+the+team;Every+contribution+counts&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

欢迎贡献！请随时提交 Pull 请求。

1. 分叉存储库。
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)。
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)。
4. 推送到分支 (`git push origin feature/AmazingFeature`)。
5. 打开拉取请求。





---




<div align="center">

## 免责声明

<img src="https://readme-typing-svg.demolab.com?lines=Read+this+before+you+break+something;You%27ve+been+warned;Backup+first%21;With+great+power...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>
**使用此工具的风险由您自行承担。在进行任何修改之前，请务必备份您的保存文件。**

开发人员对任何保存数据丢失或使用此工具可能出现的问题不承担任何责任。





---




<div align="center">

## 支持

<img src="https://readme-typing-svg.demolab.com?lines=We%27ve+got+your+back;Need+help%3F;We%27re+here+for+you&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

- **Discord：** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub 问题：** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Nexus 模组：** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## 许可证

<img src="https://readme-typing-svg.demolab.com?lines=MIT+%E2%80%94+do+whatever+you+want;Free+as+in+beer;Open+source%2C+open+mind&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

该项目已获得 MIT 许可 - 有关详细信息，请参阅 [license](license) 文件。





---




<div align="center">

## Palworld 团队

<img src="https://readme-typing-svg.demolab.com?lines=The+people+behind+the+magic;Meet+the+team;Built+with+passion&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

如果没有背后的人，这个项目就不会存在。

**[Pylar](https://github.com/deafdudecomputers)** — 这一切的始作俑者。这个工具的每一行都可以追溯到他对保存引擎、GUI 和您每天使用的功能的愿景和不懈的工作。

**[cyrix](https://github.com/CyrixJD115)** — 重构者和子维护者。专注于代码质量、简化和结构改进——随着项目的发展，保持代码库干净、更小、更易于维护。

**[dkoz](https://github.com/dkoz)** — ID 背后的人。提供游戏数据 ID、对 ID 代码的结构洞察，以及对 Palworld 数据如何连接在一起的深入了解，从而使工具在每次游戏更新时保持准确。

**[oMaN-Rod](https://github.com/oMaN-Rod)** — 提供了该项目派生的原始保存解析器。如果没有他在破解 Palworld 保存格式方面的基础工作，这一切都不会存在。该分支简化了他的解析器，成为今天的 PST。





---




<div align="center">

## 致谢

<img src="https://readme-typing-svg.demolab.com?lines=Where+credit+is+due;Thank+you+all;We+stand+on+shoulders&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

非常感谢：

- **Palworld** 由 Pocketpair, Inc. 开发 - 这款游戏将我们所有人聚集在一起。
- **错误报告者** - 提交的每个问题、发现的每个边缘案例、粘贴在 Discord 中的每条日志。您可以通过每个报告使该工具更加强大。
- **Palworld 模组社区** — 模组作者、工具开发者和修补者，他们分享知识、逆向工程格式并推动生态系统向前发展。这个项目是建立在集体努力的基础上的。
- **所有贡献者和社区成员** - 无论您是提交了 PR、在 Discord 中回答了问题，还是只是向朋友介绍了 PST - 谢谢。

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**用 ❤️ 为 Palworld 社区制作**

[⬆ Back to Top](#palworld-save-tools)

</div>