# Phigros Save Manager v2.0

Phigros v3.19.4 存档管理工具，支持命令行和图形界面。

## 依赖

```bash
pip install pycryptodome
```

## 快速使用

### GUI（推荐）

双击 `run_gui.py` 打开图形界面：

- 打开/保存/新建/导入/导出存档
- 搜索和分类过滤（成绩、歌曲、收藏、章节等）
- 快捷操作：全满分、消除红点、补全章节进度、补全 AT/INSGrade
- 右键编辑/删除条目

或命令行启动：

```bash
python run_gui.py
python run_gui.py savedata.xml    # 打开指定存档
```

### CLI

```bash
# 零配置生成全满分全解锁存档
python -m phigros_save_tool.cli build-full output.xml --rank 551

# 基于现有存档修改
python -m phigros_save_tool.cli build-from my_save.xml output.xml --rank 551

# 拆包 APK
python -m phigros_save_tool.cli unpack Phigros-v3.19.4.apk ./extracted

# 加解密
python -m phigros_save_tool.cli decrypt playerprefs.xml data.json
python -m phigros_save_tool.cli encrypt data.json playerprefs.xml
```

---

## 参数说明

| 命令 | 说明 |
|------|------|
| `build-full <out>` | 零配置全存档 |
| `build-from <base> <out>` | 基于现有存档修改 |
| `unpack <apk> <dir>` | 拆包 APK |
| `decrypt <in.xml> <out.json>` | 解密 |
| `encrypt <in.json> <out.xml>` | 加密 |

**`--rank`** — 课题模式等级，格式：百位颜色 + 十位个位等级

| 值 | 颜色 |
|----|------|
| 1xx | 🟢 绿 |
| 2xx | 🔵 蓝 |
| 3xx | 🔴 红 |
| 4xx | 🟡 金 |
| 5xx | 🌈 彩 |

例：`551` = 彩色 51 级，`230` = 蓝色 30 级。

---

## 成绩格式

```json
{"s": 分数, "a": 准确率, "c": 评估码}
```

| c 值 | 含义 |
|------|------|
| 2 | AP（All Perfect） |
| 1 | FC（Full Combo） |
| 0 | Clear |

满分：`{"s":1000000,"a":100.0,"c":2}`

---

## 打包为 EXE

需要安装 PyInstaller：

```bash
pip install pyinstaller
```

打包 GUI：

```bash
pyinstaller --onefile --name PhigrosSaveManager run_gui.py
```

生成的 `PhigrosSaveManager.exe` 在 `dist/` 目录下，可直接运行。

---

## 注意事项

1. 导入前务必备份设备端存档
2. 导入后断网，避免云存档覆盖
3. 1key 收藏品的值必须与 key-store 的 target_count 一致
4. 本工具仅供学习和研究用途
