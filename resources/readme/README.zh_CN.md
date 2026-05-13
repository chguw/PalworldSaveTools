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

## 目录

- [特点](#特点)
- [安装](#安装)
- [快速入门](#快速入门)
- [工具概述](#工具概述)
- [指南](#指南)
- [故障排除](#故障排除)
- [构建独立可执行文件（仅限 Windows）](#构建独立可执行文件仅限-windows)
- [贡献](#贡献)
- [许可证](#许可证)

---

## 特点

### 核心功能

|特色 |描述 |
|---------|-------------|
| **快速保存解析** |最快的保存文件阅读器之一 |
| **玩家管理** |查看、编辑、重命名、更改级别、解锁技术和管理玩家 |
| **公会管理** |创建、重命名、移动玩家、解锁实验室研究以及管理公会 |
| **Pal Editor** |统计、技能、IVs、等级、灵魂、性别、老板/幸运切换的完整编辑器 |
| **大本营工具** |导出、导入、克隆、调整半径和管理基地 |
| **地图查看器** |带有坐标和详细信息的交互式基地和玩家地图 |
| **角色转移** |在不同世界/服务器之间转移角色（交叉保存）|
| **保存转换** |在 Steam 和 GamePass 格式之间转换 |
| **世界设置** |编辑 WorldOption 和 LevelMeta 设置 |
| **时间戳工具** |修复负时间戳并重置玩家时间 |

### 多合一工具

**一体化工具**套件提供全面的保存管理：

- **删除工具**
  - 删除玩家、基地或公会
  - 根据时间阈值删除不活跃玩家
  - 删除重复的玩家和空的公会
  - 删除未引用/孤立数据

- **清理工具**
  - 删除无效/修改的项目
  - 删除无效的pals和passives
  - 修复非法的pals（上限为合法的最大统计数据）
  - 删除无效结构
  - 重置防空炮塔
  - 解锁private chests

- **公会工具**
  - 重建所有公会
  - 在公会之间移动玩家
  - 使玩家公会领袖
  - 重命名公会
  - 最高公会等级
  - 解锁所有实验室研究

- **玩家工具**
  - 编辑玩家pal统计数据和技能
  - 解锁所有技术
  - 解锁观察笼
  - 升级/降低玩家等级
  - 重命名玩家

- **保存实用程序**
  - 重置任务
  - 重置地下城
  - 修复时间戳
  - 修剪过剩的库存
  - 生成 PalDefender 命令

### 附加工具

|工具|描述 |
|------|-------------|
| **编辑玩家Pals** |完整的pal editor，包含统计数据、技能、IVs、天赋、灵魂、等级和性别|
| **SteamID 转换器** |将 Steam ID 转换为 Palworld UID |
| **修复主机保存** |在两个玩家之间交换 UID（例如，用于主机交换） |
| **槽式注入器** |增加每位玩家的 palbox 槽位 |
| **恢复地图** |在所有世界/服务器上应用解锁的地图进度 |
| **重命名世界** |在 LevelMeta 中更改世界名称 |
| **世界选项编辑器** |编辑世界设置和配置 |
| **关卡元编辑器** |编辑世界元数据（名称、主机、级别）|

---

## 安装

### 先决条件

**对于独立版 (Windows)：**
- Windows 10/11
- [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version) (2015-2022)

**对于从源代码运行（所有平台）：**
- Python 3.11 或更高版本

### 独立（Windows - 推荐）

1. 从[GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)下载最新版本
2. 解压zip文件
3.运行`PalworldSaveTools.exe`

### 来自源头（所有平台）

启动脚本会自动创建虚拟环境并安装所有依赖项。

**使用uv：**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv venv --python 3.12
uv run start.py
```

**Windows：**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
start_win.cmd
```

**Linux：**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
chmod +x start_linux.sh
./start_linux.sh
```

### 分支机构

- **稳定**（推荐）：`git clone https://github.com/deafdudecomputers/PalworldSaveTools.git`
- **测试版**（最新功能）：`git clone -b beta https://github.com/deafdudecomputers/PalworldSaveTools.git`

---

## 快速入门

1. **加载您的保存**
   - 单击标题中的菜单按钮
   - 选择**加载保存**
   - 导航到您的 Palworld 保存文件夹
   - 选择`Level.sav`

2. **探索您的数据**
   - 使用选项卡查看玩家、公会、基地或地图
   - 搜索和过滤以查找特定条目

3. **做出改变**
   - 选择要编辑、删除或修改的项目
   - 右键单击可显示带有附加选项的上下文菜单

4. **保存您的更改**
   - 单击菜单按钮 → **保存更改**
   - 自动创建备份

---

## 工具概述

### 多合一工具 (AIO)

全面保存管理的主界面有五个选项卡：

**玩家库存选项卡** - 查看和管理服务器上所有玩家的库存
- 编辑玩家统计数据、库存、装备。
- 能够编辑质量、添加、删除库存和装备中的任何东西。

**基地库存选项卡** - 查看和管理服务器上所有基地的库存。
- 编辑基本库存。
- 能够清理容器、编辑质量、添加或删除基础库存中的任何内容。
- 过滤任何可能的作弊行为。

**玩家选项卡** - 查看和管理服务器上的所有玩家
- 编辑玩家姓名、等级和 pal 计数
- 删除不活跃的玩家
- 查看玩家公会和最后在线时间

**公会选项卡** - 管理公会及其基地
- 重命名公会，更换领导者
- 查看基地位置和等级
- 删除空的或不活跃的公会

**基地选项卡** - 查看所有基地营
- 导出/导入基础蓝图
- 克隆基地到其他公会
- 调整基础半径

### 地图查看器

您的世界的交互式可视化：
- 查看所有基地位置和玩家位置
- 按公会或玩家名称过滤
- 单击标记以获取详细信息
- 为 PalDefender 生成 `killnearestbase` 命令

### 角色转移

在不同世界/服务器之间转移角色（交叉保存）：
- 转移单个或所有玩家
- 保留角色、pals、库存和技术
- 对于在合作服务器和专用服务器之间迁移很有用

### 修复主机保存

在两个玩家之间交换 UID：
- 将进度从一名玩家转移到另一名玩家
- 对于主机/合作社到服务器的传输至关重要
- 对于在玩家之间交换主机角色很有用
- 对于平台交换很有用（Xbox ↔ Steam）
- 解决主机/服务器 UID 分配问题
- **注意：** 受影响的玩家必须首先在目标保存中创建角色

---

## 指南

### 保存文件位置

**主机/合作社：**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**专用服务器：**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### 地图解锁

<details>
<summary>点击展开地图解锁说明</summary>

1. 从 `resources\` 复制 `LocalData.sav`
2.找到你的服务器/世界保存文件夹
3.用复制的文件替换现有的`LocalData.sav`
4. 使用完全解锁的地图启动游戏

> **注意：** 使用“工具”选项卡中的“恢复地图”工具，通过自动备份将解锁的地图一次性应用到您的所有世界/服务器。

</details>

### 主机→服务器传输

<details>
<summary>点击展开主机到服务器传输指南</summary>

1.从主机保存复制`Level.sav`和`Players`文件夹
2. 粘贴到专用服务器保存文件夹
3.启动服务器，创建新角色
4.等待自动保存，然后关闭
5. 使用 **Fix Host Save** 迁移 GUID
6. 将文件复制回来并启动

**使用修复主机保存：**
- 从临时文件夹中选择 `Level.sav`
- 选择**旧角色**（来自原始保存）
- 选择**新角色**（您刚刚创建）
- 单击**迁移**

</details>

### 主机交换（更改主机）

<details>
<summary>点击展开主机交换指南</summary>

**背景：**
- 主机始终使用 `0001.sav` — 无论主机是谁，都使用相同的 UID
- 每个客户端使用唯一的常规 UID 保存（例如 `123xxx.sav`、`987xxx.sav`）

**先决条件：**
两名玩家（旧主机和新主机）都必须生成常规保存。这是通过加入主机的世界并创建一个新角色来实现的。

**步骤：**

1. **确保定期保存存在**
   - 玩家 A（旧主机）应该定期保存（例如 `123xxx.sav`）
   - 玩家 B（新主机）应该定期保存（例如 `987xxx.sav`）

2. **将旧主机的主机保存交换为常规保存**
   - 使用PalworldSaveTools **修复主机保存**来交换：
   - 老主机的 `0001.sav` → `123xxx.sav`
   -（这会将旧主机的进度从主机位置移至其常规玩家位置）

3. **将新主机的常规存档交换为主机存档**
   - 使用PalworldSaveTools **修复主机保存**来交换：
   - 新主机的 `987xxx.sav` → `0001.sav`
   -（这会将新主机的进度移至主机槽中）

**结果：**
- 玩家 B 现在是主机，拥有自己的角色和 `0001.sav` 中的 pals
- 玩家 A 成为客户，并拥有 `123xxx.sav` 的原始进度

</details>

### 基础导出/导入

<details>
<summary>点击展开底座导出/导入指南</summary>

**导出基地：**
1. 在 PST 中加载您的保存内容
2. 转到“基地”选项卡
3. 右键单击一个基地 → 导出基地
4.另存为`.json`文件

**导入基础：**
1. 转到“基地”选项卡或“基地地图查看器”
2. 右键单击要导入基地的公会
3. 选择导入基地
4. 选择导出的 `.json` 文件

**克隆基地：**
1. 右键单击一个基地 → 克隆基地
2.选择目标公会
3. 基地将被克隆并偏移定位

**调整基础半径：**
1. 右键单击底座 → 调整半径
2. 输入新半径（50% - 1000%）
3. 保存并加载游戏中的存档以重新分配结构

</details>

---

## 故障排除

### “未找到 VCRUNTIME140.dll”

**解决方案：** 安装[Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version)

### `struct.error` 解析时保存

**原因：** 保存文件格式过时

**解决方案：**
1. 在游戏中加载存档（单人、合作或专用服务器模式）
2. 这会触发自动结构更新
3.确保存档在最新游戏补丁时或之后更新

### GamePass 转换器不工作

**解决方案：**
1.关闭Palworld的GamePass版本
2. 等待几分钟
3.运行Steam→GamePass转换器
4. 在GamePass上启动Palworld进行验证

---

## 构建独立可执行文件（仅限 Windows）

运行构建脚本以创建独立的可执行文件：

```bash
scripts\build.cmd
```

这将在项目根目录中创建 `PST_standalone_v{version}.7z` 。

---

## 贡献

欢迎贡献！请随时提交 Pull 请求。

1. 分叉存储库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4.推送到分支(`git push origin feature/AmazingFeature`)
5. 发起拉取请求

---

## 免责声明

**使用此工具的风险由您自行承担。在进行任何修改之前，请务必备份您的保存文件。**

开发人员对任何保存数据丢失或使用此工具可能出现的问题不承担任何责任。

---

## 支持

- **Discord：** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub 问题：** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **文档：** [Wiki](https://github.com/deafdudecomputers/PalworldSaveTools/wiki) *（目前正在开发中）*

---

## 许可证

该项目根据 MIT 许可证获得许可 - 有关详细信息，请参阅 [LICENSE](LICENSE) 文件。

---

## 致谢

- **Palworld** 由 Pocketpair, Inc. 开发。
- 感谢所有帮助改进此工具的贡献者和社区成员

---

<div align="center">

**用 ❤️ 为 Palworld 社区制作**

[⬆ Back to Top](#palworldsavetools)

</div>