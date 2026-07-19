# Phigros Save Tool 视频介绍提示词

## 通用视频生成提示词（适用于 Sora / Kling / Runway）

**中文提示词：**

```
一部科技感十足的软件项目介绍短视频，时长约 60 秒。

场景 1（开场 0-5s）：深蓝色渐变背景，粒子光点从屏幕中央汇聚，形成 Phigros 音符图标，随后文字"Phigros Save Manager v2.0"以金属质感浮现，下方小字"APK 拆包 · 解密 · 加密 · 自定义存档"。镜头缓慢推进。

场景 2（功能展示 5-20s）：分屏动画。左侧显示 APK 文件被解压，弹出 catalog.json、songs.json、key-store.json 等文件列表；右侧显示加密的 XML 文件经过 AES-256-CBC 解密，变成可读的 JSON 数据，键值对以发光节点形式排列。画面中出现命令行终端窗口，白色代码在黑色背景上快速输入："phigros-save build-full output.xml --rank 551"，回车后输出统计信息。

场景 3（核心特性 20-40s）：三个卡片依次飞入。第一张卡片标题"零配置构建"，内容"一行命令生成全满分全解锁存档"；第二张"基线修改"，内容"保留现有设置，补全成绩和解锁"；第三张"配置文件精确控制"，内容"songs.json + key-store.json + settings.json"。每张卡片带有绿色勾选动画。

场景 4（技术细节 40-50s）：展示加密密钥的十六进制字符串流动效果，AES-256-CBC 算法名称以霓虹灯风格出现。接着展示成绩记录格式 {"s":1000000,"a":100.0,"c":2}，数字逐个高亮。课题模式等级编码表以表格形式展开：百位颜色（绿蓝红金彩）+ 十位个位等级。

场景 5（结尾 50-60s）：GitHub 仓库页面截图风格，stars 和 forks 图标闪烁。最终画面回到 Phigros 音符图标，下方显示项目地址 "github.com/zhangyou901105/phigros-save-tool"，渐隐结束。

整体风格：深色科技风，主色调深蓝/黑/青绿，字体使用等宽编程字体，动效流畅专业。背景音乐为轻快的电子节拍，配合画面切换节奏。
```

---

**英文提示词（适用于 Sora / Runway）：**

```
A tech-style software project introduction video, approximately 60 seconds long.

Scene 1 (Intro 0-5s): Deep blue gradient background, particle lights converge from center forming the Phigros music note icon, then the text "Phigros Save Manager v2.0" appears with metallic texture. Subtitle: "APK Unpack · Decrypt · Encrypt · Custom Save". Camera slowly pushes forward.

Scene 2 (Features 5-20s): Split-screen animation. Left side shows an APK file being unpacked, revealing catalog.json, songs.json, key-store.json files. Right side shows encrypted XML flowing through an AES-256-CBC decryption pipeline, transforming into readable JSON data with glowing node connections. A terminal window appears showing the command "phigros-save build-full output.xml --rank 551" being typed, followed by statistics output.

Scene 3 (Core Features 20-40s): Three cards fly in sequentially. Card 1: "Zero-Config Build" — "One command to generate full-score full-unlock save". Card 2: "Baseline Modification" — "Keep existing settings, add scores and unlocks". Card 3: "Precise Control" — "songs.json + key-store.json + settings.json". Each card gets a green checkmark animation.

Scene 4 (Technical Details 40-50s): Hexadecimal encryption keys flow across screen. "AES-256-CBC" appears in neon style. Score record format {"s":1000000,"a":100.0,"c":2} highlights each field. ChallengeModeRank encoding table expands: hundreds digit color (green/blue/red/gold/colorful) + tens/ones digit level.

Scene 5 (Outro 50-60s): GitHub repository page style, stars and forks icons sparkle. Final frame returns to Phigros music note icon with URL "github.com/zhangyou901105/phigros-save-tool", fade out.

Style: Dark tech aesthetic, deep blue/black/cyan-green palette, monospace programming font, smooth professional animations. Light electronic beat music synced to scene transitions.
```

---

## 分镜脚本（供剪辑参考）

| 时间 | 画面 | 文字/旁白 | 转场 |
|------|------|-----------|------|
| 0-5s | 粒子汇聚成音符 → 标题 | "Phigros Save Manager v2.0" | 淡入 |
| 5-10s | APK 解压动画 | "版本拆包" | 滑动 |
| 10-15s | XML→JSON 解密过程 | "解密存档" | 滑动 |
| 15-20s | 终端输入命令 | "一键加密" | 闪切 |
| 20-30s | 三张功能卡片 | "零配置 / 基线法 / 精确控制" | 飞入 |
| 30-40s | 密钥/成绩格式/等级编码 | "AES-256-CBC" | 缩放 |
| 40-50s | GitHub 页面 | "开源 · MIT License" | 拉远 |
| 50-60s | 结尾 Logo + URL | 项目地址 | 淡出 |

---

## 旁白文案（可选）

```
Phigros Save Manager，专为 Phigros v3.19.4 设计的完整存档管理工具。

支持 APK 拆包，自动提取歌曲目录和解锁键配置。
支持存档解密和加密，AES-256-CBC 算法，完整还原游戏格式。

新增零配置构建功能——一行命令即可生成全满分、全解锁、彩色 51 级存档。
也可以基于现有存档修改，保留你的设置，只补全成绩和解锁状态。

所有代码开源，MIT 协议。
访问 GitHub 获取源码和详细文档。
```

---

## 生成建议

| 平台 | 推荐参数 |
|------|----------|
| **Sora** | 使用英文提示词，时长 60s，比例 16:9，风格 Cinematic |
| **Kling** | 使用中文提示词，时长 15s×4 段拼接，比例 16:9 |
| **Runway Gen-3** | 分段生成各场景，使用英文提示词，每段 5s |
| **Pika** | 适合生成单个动态镜头，如密钥流动、卡片飞入 |
| **剪映/CapCut** | 适合后期合成，配合模板和字幕 |

**最佳方案：** 用 Kling/Sora 生成各场景素材 → 剪映拼接 → 添加旁白和字幕 → 导出。
