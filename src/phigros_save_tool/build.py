"""自定义存档构建模块。

根据配置文件夹生成完整加密存档。
"""

import json
import os
from pathlib import Path
from typing import Optional

from .crypto import Keys, encrypt_to_playerprefs_xml


def build_custom_save(
    config_dir: str,
    output_path: str,
    challenge_rank: str = "551",
    game_completed: str = "3.0",
    key_store: Optional[list[dict]] = None,
    record_map: Optional[list[dict]] = None,
) -> dict[str, str]:
    """根据配置文件夹构建完整加密存档。

    Args:
        config_dir: 配置目录路径
        output_path: 输出 XML 路径
        challenge_rank: 课题模式等级
                       百位=颜色(1绿/2蓝/3红/4金/5彩)
                       十位+个位=等级。例: 551=彩色51级
        game_completed: GameCompleted 值（"3.0"跳过首次加载）
        key_store: 可选，直接传入 key-store.json 数据
        record_map: 可选，直接传入 record-key-map.json 数据

    Returns:
        构建完成的 entries 字典

    Config dir 结构:
        config_dir/
        ├── songs.json          — 歌曲成绩配置
        ├── key-store.json      — 解锁键配置（可选，自动补全）
        └── settings.json       — 额外设置（可选）
    """
    config_dir = str(Path(config_dir).resolve())
    output_path = str(Path(output_path).resolve())

    # 加载 key_store
    if key_store is None:
        ks_path = os.path.join(config_dir, "key-store.json")
        if os.path.exists(ks_path):
            with open(ks_path, "r", encoding="utf-8") as f:
                key_store = json.load(f)
        else:
            key_store = []

    # 加载 songs.json
    songs_config: list[dict] = []
    songs_path = os.path.join(config_dir, "songs.json")
    if os.path.exists(songs_path):
        with open(songs_path, "r", encoding="utf-8") as f:
            songs_config = json.load(f)

    # 加载 settings.json
    settings: dict = {}
    settings_path = os.path.join(config_dir, "settings.json")
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)

    # 构建条目
    entries: dict[str, str] = {}

    # 1. 成绩记录
    FULL_SCORE = json.dumps(
        {"s": 1000000, "a": 100.0, "c": 2}, separators=(",", ":")
    )
    for song in songs_config:
        if isinstance(song, dict):
            if "playerprefs_key" in song:
                entries[song["playerprefs_key"]] = song.get(
                    "value", FULL_SCORE
                )
            elif "name" in song and "variant" in song:
                name = song["name"]
                variant = song["variant"]
                score = song.get("score", 1000000)
                acc = song.get("acc", 100.0)
                clear = song.get("clear", 2)
                entries[f"{name}.0.Record.{variant}"] = json.dumps(
                    {"s": score, "a": acc, "c": clear}, separators=(",", ":")
                )

    # 2. 解锁键
    ks_dict = {k["playerprefs_key"]: k for k in key_store} if key_store else {}
    for sk in key_store:
        key = sk["playerprefs_key"]
        kind = sk.get("kind", 0)
        target_count = sk.get("target_count", 1)

        if kind == 0:  # 歌曲
            entries[key] = str(target_count)
        elif kind == 1:  # 收藏
            entries[key] = str(target_count)
        elif kind == 2:  # 插画
            entries[key] = "1"
        elif kind == 3:  # 头像
            entries[key] = "1"

    # 3. CollectionTextOpened（消除红点）
    for sk in key_store:
        if sk.get("kind") == 1:
            key = sk["playerprefs_key"]
            tc = sk.get("target_count", 1)
            ct_key = key.replace("1key", "") + "CollectionTextOpened"
            entries[ct_key] = str(max(tc, 2))

    # 4. 章节/特殊解锁标志
    entries["GameCompleted"] = game_completed
    entries["finishLegacyChapter"] = "True"
    entries["completed"] = "312"
    entries["chapter8Passed"] = "True"
    entries["chapter8UnlockBegin"] = "True"
    entries["chapter8UnlockSecondPhase"] = "True"
    entries["challengeModeRank"] = challenge_rank

    for i in range(6):
        entries[f"chapter8SongUnlocked[{i}]"] = "True"
        entries[f"randomVersionUnlocked[{i}]"] = "True"

    c8_keys = [
        "C8CraveWaveUnlocked",
        "C8DESTRUCTION321Unlocked",
        "C8DistortedFateUnlocked",
        "C8LuminescenceUnlocked",
        "C8RetributionUnlocked",
        "C8TheChariotREVIIVALUnlocked",
    ]
    for ck in c8_keys:
        entries[ck] = "True"

    at_songs = ["Igallta", "Rrharil", "Spasmodic"]
    for song in at_songs:
        for diff in ["EZ", "HD", "IN", "AT"]:
            entries[f"unlockFlagOf{song}{diff}"] = "True"

    ins_songs = [
        "Cuvism",
        "DESTRUCTION321",
        "DistortedFate",
        "Shadow",
        "Stasis",
        "YouaretheMiserable",
        "atruthseekerCommunicationwithUtopiawillbelost",
        "iLArtifact",
        "inferior",
        "心之所向",
    ]
    for song in ins_songs:
        entries[f"{song}INSGrade"] = "True"

    # 5. 合并用户设置
    entries.update(settings)

    # 6. 加密输出
    size = encrypt_to_playerprefs_xml(entries, output_path)
    print(f"[build] Encrypted: {size:,} bytes -> {output_path}")
    print(f"[build] Total entries: {len(entries)}")

    return entries
