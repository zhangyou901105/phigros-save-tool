# Phigros Save Manager v2.0

> Phigros v3.19.4 完整存档管理工具 — 从 APK 拆包歌曲数据、解密/加密存档、根据配置构建自定义存档。

## 📋 目录

- [功能](#功能)
- [安装](#安装)
- [快速开始](#快速开始)
- [命令行用法](#命令行用法)
- [Python API](#python-api)
- [存档格式详解](#存档格式详解)
- [配置文件说明](#配置文件说明)
- [密钥信息](#密钥信息)
- [项目结构](#项目结构)
- [开发](#开发)
- [注意事项](#注意事项)

---

## 功能

| 功能 | 说明 |
|------|------|
| **APK 拆包** | 从 APK 提取 `catalog.json`、`songs.json`、`key-store.json`、谱面 bundle 清单 |
| **解密存档** | 将加密的 `playerprefs.xml` 还原为可读 JSON |
| **加密存档** | 将可读 JSON 加密为 `playerprefs.xml` |
| **零配置构建** | 一行命令生成全满分全解锁存档（自动加载数据文件） |
| **基线构建** | 以现有存档为模板，保留设置，补满分成绩和解锁 |
| **配置构建** | 通过 `songs.json` + `key-store.json` + `settings.json` 精确控制 |

---

## 安装

```bash
# 克隆仓库
git clone https://github.com/zhangyou901105/phigros-save-tool.git
cd phigros-save-tool

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# 安装依赖
pip install -e ".[dev]"
```

### 依赖

- Python ≥ 3.10
- pycryptodome ≥ 3.18.0

---

## 快速开始

### 1. 拆包 APK

```bash
phigros-save unpack Phigros-v3.19.4.apk ./extracted
```

输出文件：
```
extracted/
├── catalog.json              — Addressables 目录
├── songs_from_catalog.json   — 解析后的歌曲列表
├── songs.json                — 歌曲信息
├── key-store.json            — 解锁键配置
└── bundle_manifest.json      — 谱面资源清单
```

### 2. 解密现有存档

```bash
# 从设备导出 playerprefs.xml 后
phigros-save decrypt com.PigeonGames.Phigros.v2.playerprefs.xml savedata.json
```

输出摘要：
```
[decrypt] Decrypted: 2062 entries
[decrypt] Records: 984
[decrypt] Song keys (0key): 143
[decrypt] Collection keys (1key): 285
...
```

### 3. 构建存档

```bash
# 零配置：一行搞定全满分全解锁存档（自动加载 key-store.json 和 record-key-map.json）
phigros-save build-full output.xml --rank 551

# 基于现有存档修改（保留设置，补满分成绩）
phigros-save build-from my_save.xml output.xml --rank 551

# 精确控制（配置文件法）
phigros-save build-config ./my-config/ output.xml
```

---

## 命令行用法

```
phigros-save <command> [options]

Commands:
  unpack        从 APK 拆包歌曲数据
  decrypt       解密 playerprefs.xml 为 JSON
  encrypt       加密 JSON 为 playerprefs.xml
  build-full    零配置：一行生成全满分全解锁存档
  build-from    基线法：以现有存档为模板修改
  build-config  配置文件法：精确控制存档内容
```

### build-full（零配置）

```bash
# 一行搞定，自动加载 key-store.json + record-key-map.json
phigros-save build-full output.xml --rank 551

# 自定义玩家名
phigros-save build-full output.xml --rank 230 --player-name "Arlec"

# 基于现有存档保留设置
phigros-save build-full output.xml --baseline my_save.xml
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--rank` | `551` | 课题模式等级（百位=颜色，十位+个位=等级） |
| `--game-completed` | `3.0` | GameCompleted 值 |
| `--player-name` | 无 | 玩家名称 |
| `--baseline` | 无 | 基线存档 XML，保留其设置项 |

---

## Python API

```python
from phigros_save_tool import (
    Keys,                          # 密钥常量
    decrypt_playerprefs_xml,       # XML → dict
    encrypt_to_playerprefs_xml,    # dict → XML
    build_custom_save,             # 配置文件夹 → 加密 XML（旧 API，保留兼容）
    build_full_save,               # 零配置全存档构建（推荐）
    build_from_baseline,           # 基线法修改存档（推荐）
    unpack_apk,                    # APK → 提取文件
)

# 解密
entries, failed = decrypt_playerprefs_xml("savedata.xml")
print(f"Decrypted {len(entries)} entries, {len(failed)} failed")

# 加密
size = encrypt_to_playerprefs_xml(entries, "output.xml")
print(f"Encrypted: {size:,} bytes")

# 零配置构建（推荐）
build_full_save(
    output_path="output.xml",
    challenge_rank="551",
    player_name="Arlec",
)

# 基线法构建（推荐）
build_from_baseline(
    baseline_path="my_save.xml",
    output_path="output.xml",
    rank="551",
)

# 拆包 APK
unpack_apk("Phigros-v3.19.4.apk", "./extracted")
```

---

## 存档格式详解

### 加密方式

**PlayerPrefs XML（主存档）：** AES-256-CBC，PKCS7 填充

```
XML text → URL unquote → Base64 decode → AES-256-CBC decrypt → PKCS7 unpad → UTF-8
```

### 成绩记录格式

```json
{"s": 分数, "a": 准确率, "c": 评估码}
```

| 字段 | 含义 | AP 值 | FC 值 | Clear |
|------|------|-------|-------|-------|
| `s` | 实际分数 | `1000000` | `1000000` | 真实分数 |
| `a` | 准确率% | `100.0` | `100.0` | 真实 ACC |
| `c` | 评估码 | `2` | `1` | `0` |

### 解锁键系统

| 类型 | 前缀 | 数量 | 值规则 |
|------|------|------|--------|
| 歌曲 | `0key` | 143 | `target_count`（固定 1） |
| 收藏 | `1key` | 285 | `key_store.json` 的 `target_count`（1~7） |
| 插画 | `2key` | 312 | 固定 `1` |
| 头像 | `3key` | 109 | 固定 `1` |

**⚠️ 重要：** 1key 收藏品的值必须与 `key_store.json` 中的 `target_count` 精确匹配，不能全部填 1。

### CollectionTextOpened（红点标记）

| 键格式 | `{收藏名}CollectionTextOpened` |
|--------|-------------------------------|
| 值 = 1 | 未读（左上角红点） |
| 值 ≥ 2 | 已读（无红点） |

建议将所有值设为 `max(target_count, 2)` 以消除红点。

### ChallengeModeRank 编码

| 位数 | 含义 | 值 | 颜色 |
|------|------|-----|------|
| 百位 | 颜色 | 1 | 🟢 绿 |
| | | 2 | 🔵 蓝 |
| | | 3 | 🔴 红 |
| | | 4 | 🟡 金 |
| | | 5 | 🌈 彩 |
| 十位+个位 | 等级 | 01~99 | 难度等级 |

**示例：**
| 值 | 解析 | 说明 |
|----|------|------|
| `230` | 蓝 + 30级 | 蓝色30 |
| `551` | 彩 + 51级 | 彩色51 |
| `499` | 金 + 99级 | 金色99 |

**公式：** `ChallengeModeRank = 颜色×100 + 等级`

---

## 配置文件说明

### songs.json

```json
[
  {
    "name": "Glaciaxion",
    "variant": "EZ",
    "score": 1000000,
    "acc": 100.0,
    "clear": 2
  },
  {
    "playerprefs_key": "MARENOL.LeaF.0.Record.HD",
    "value": "{\"s\":1000000,\"a\":100.0,\"c\":2}"
  }
]
```

两种格式：
1. **简化格式**：`name` + `variant` + `score`/`acc`/`clear`
2. **完整格式**：`playerprefs_key` + `value`（JSON 字符串）

### settings.json

```json
{
  "playerName": "Player",
  "playerIcon": 0,
  "playerTitle": 0,
  "musicVolume": 1,
  "SEVolume": 1,
  "offset": 0,
  "chordSupport": true,
  "hitFxIsOn": true,
  "noteScale": 1,
  "dspSliderValue": 2,
  "autoSync": false,
  "readPrivacyPolicy": 1,
  "playerIDUpdated": true,
  "playerID": "GUEST"
}
```

### key-store.json

从 APK 拆包获得，或从 `data/key-store-v3.19.4.json` 复制。

---

## 密钥信息

### PlayerPrefs XML

```
KEY = 0x627ff1942185e011c815e81e639b9a00001c766b826c29bd96578589f19a6fd6
IV  = 0xbe56167f83da3befeff81861a5c5f3cd
```

### ZIP 五模块

```
KEY = Base64Decode("6Jaa0qVAJZuXkZCLiOa/Ax5tIZVu+taKUN1V1nqwkks=")
IV  = Base64Decode("Kk/wisgNYwcAV8WVGMgyUw==")
```

---

## 项目结构

```
phigros-save-tool/
├── pyproject.toml          — 项目配置
├── README.md               — 本文件
├── src/
│   └── phigros_save_tool/
│       ├── __init__.py     — 公共 API
│       ├── crypto.py       — 加密/解密核心
│       ├── unpack.py       — APK 拆包
│       ├── build.py        — 自定义存档构建
│       └── cli.py          — 命令行入口
├── examples/
│   ├── songs.json          — 示例成绩配置
│   ├── settings.json       — 示例设置
│   └── key-store.json      — 示例 key-store
├── tests/
│   ├── test_crypto.py      — 加密/解密测试
│   └── test_build.py       — 构建测试
└── docs/
    └── API.md              — API 文档
```

---

## 开发

```bash
# 运行测试
pytest tests/ -v

# 代码检查
ruff check src/ tests/

# 格式化
ruff format src/ tests/
```

---

## 注意事项

1. **备份原存档** — 导入前务必备份设备端存档
2. **断网导入** — 导入后不要联网，避免云存档覆盖
3. **权限修复** — 导入后需修复文件所有权（`chown 10188:10188`）
4. **1key 收藏值** — 必须与 `key_store.json` 的 `target_count` 一致
5. **密码学免责声明** — 本工具仅供学习和研究用途

---

*基于 Phigros v3.19.4 逆向工程（Il2CppDumper + ARM64 控制流分析）*
