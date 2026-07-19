"""CLI 命令行入口。

优化后支持三种 build 模式:
  # 零配置：一行搞定
  phigros-save build-full my_save.xml --rank 551

  # 以现有存档为基线修改
  phigros-save build-from baseline.xml my_save.xml --rank 551

  # 精确控制（配置文件法）
  phigros-save build-config ./config/ output.xml
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from .crypto import Keys, decrypt_playerprefs_xml, encrypt_to_playerprefs_xml
from .unpack import unpack_apk
from .build import build_custom_save


# ============================================================
# 零配置全存档构建
# ============================================================

def build_full_save(
    output_path: str,
    rank: str = "551",
    game_completed: str = "3.0",
    player_name: Optional[str] = None,
    key_store_path: Optional[str] = None,
    record_map_path: Optional[str] = None,
    baseline_path: Optional[str] = None,
) -> str:
    """一行命令生成全满分全解锁存档。

    Args:
        output_path: 输出 XML 路径
        rank: 课题模式等级
        game_completed: GameCompleted 值
        player_name: 玩家名称
        key_store_path: key-store.json 路径（可选，自动查找）
        record_map_path: record-key-map.json 路径（可选，自动查找）
        baseline_path: 基线存档 XML（可选，以此为模板保留设置）
    """
    output_path = str(Path(output_path).resolve())

    # 1. 加载 key-store
    key_store = _find_or_load_key_store(key_store_path)
    print(f"[info] Key-store: {len(key_store)} keys loaded")

    # 2. 加载 record-key-map
    record_map = _find_or_load_record_map(record_map_path)
    print(f"[info] Record map: {len(record_map)} records")

    # 3. 基线存档（如果提供）
    baseline_entries: dict[str, str] = {}
    if baseline_path and os.path.exists(baseline_path):
        baseline_entries, _ = decrypt_playerprefs_xml(baseline_path)
        print(f"[info] Baseline: {len(baseline_entries)} entries loaded")

    # 4. 构建
    entries: dict[str, str] = {}

    # 从基线复制配置项
    if baseline_entries:
        for k, v in baseline_entries.items():
            if not k.startswith(("0key", "1key", "2key", "3key")) and not "Record." in k:
                entries[k] = v

    # --- 成绩 ---
    FULL_SCORE = json.dumps({"s": 1000000, "a": 100.0, "c": 2}, separators=(",", ":"))
    for rm in record_map:
        entries[rm["playerprefs_key"]] = FULL_SCORE

    # --- 解锁键 ---
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

    # --- CollectionTextOpened（消除红点） ---
    for sk in key_store:
        if sk.get("kind") == 1:
            key = sk["playerprefs_key"]
            tc = sk.get("target_count", 1)
            ct_key = key.replace("1key", "") + "CollectionTextOpened"
            entries[ct_key] = str(max(tc, 2))

    # --- 章节/特殊解锁 ---
    entries["GameCompleted"] = game_completed
    entries["finishLegacyChapter"] = "True"
    entries["completed"] = "312"
    entries["chapter8Passed"] = "True"
    entries["chapter8UnlockBegin"] = "True"
    entries["chapter8UnlockSecondPhase"] = "True"
    entries["challengeModeRank"] = rank

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
        "Cuvism", "DESTRUCTION321", "DistortedFate", "Shadow", "Stasis",
        "YouaretheMiserable", "atruthseekerCommunicationwithUtopiawillbelost",
        "iLArtifact", "inferior", "心之所向",
    ]
    for song in ins_songs:
        entries[f"{song}INSGrade"] = "True"

    # --- 用户设置 ---
    if player_name:
        entries["playerName"] = player_name
    entries["autoSync"] = "False"
    entries["readPrivacyPolicy"] = "1"
    entries["playerIDUpdated"] = "True"

    # 加密输出
    size = encrypt_to_playerprefs_xml(entries, output_path)
    stat_report(entries)
    print(f"[build] Encrypted: {size:,} bytes -> {output_path}")
    print(f"[build] Total entries: {len(entries)}")
    return output_path


def stat_report(entries: dict[str, str]) -> None:
    """打印存档统计。"""
    record_count = sum(1 for k in entries if "Record." in k)
    song_keys = sum(1 for k in entries if k.startswith("0key"))
    collection_keys = sum(1 for k in entries if k.startswith("1key"))
    illustration_keys = sum(1 for k in entries if k.startswith("2key"))
    portrait_keys = sum(1 for k in entries if k.startswith("3key"))
    print(f"[stat] Records: {record_count}")
    print(f"[stat] Song keys (0key): {song_keys}")
    print(f"[stat] Collection keys (1key): {collection_keys}")
    print(f"[stat] Illustration keys (2key): {illustration_keys}")
    print(f"[stat] Portrait keys (3key): {portrait_keys}")


# ============================================================
# 基线法构建
# ============================================================

def build_from_baseline(
    baseline_path: str,
    output_path: str,
    rank: Optional[str] = None,
    game_completed: Optional[str] = None,
    player_name: Optional[str] = None,
    key_store_path: Optional[str] = None,
    record_map_path: Optional[str] = None,
) -> str:
    """以现有存档为基线，修改部分内容。

    Args:
        baseline_path: 基线存档 XML
        output_path: 输出 XML 路径
        rank: 课题模式等级（不传则保留基线值）
        game_completed: GameCompleted（不传则保留基线值）
        player_name: 玩家名称（不传则保留基线值）
    """
    output_path = str(Path(output_path).resolve())

    # 加载基线
    baseline_entries, failed = decrypt_playerprefs_xml(baseline_path)
    print(f"[info] Baseline: {len(baseline_entries)} entries ({len(failed)} failed)")

    # 加载 key-store / record-map
    key_store = _find_or_load_key_store(key_store_path)
    record_map = _find_or_load_record_map(record_map_path)

    entries = dict(baseline_entries)

    # 覆盖成绩（补满分）
    FULL_SCORE = json.dumps({"s": 1000000, "a": 100.0, "c": 2}, separators=(",", ":"))
    for rm in record_map:
        key = rm["playerprefs_key"]
        if key not in entries:
            entries[key] = FULL_SCORE

    # 补全解锁键
    for sk in key_store:
        key = sk["playerprefs_key"]
        kind = sk.get("kind", 0)
        target_count = sk.get("target_count", 1)
        if key not in entries:
            entries[key] = str(target_count)

    # 补全 CollectionTextOpened
    for sk in key_store:
        if sk.get("kind") == 1:
            key = sk["playerprefs_key"]
            tc = sk.get("target_count", 1)
            ct_key = key.replace("1key", "") + "CollectionTextOpened"
            if ct_key not in entries:
                entries[ct_key] = str(max(tc, 2))

    # 覆盖指定值
    if rank is not None:
        entries["challengeModeRank"] = rank
    if game_completed is not None:
        entries["GameCompleted"] = game_completed
    if player_name is not None:
        entries["playerName"] = player_name

    # 加密输出
    size = encrypt_to_playerprefs_xml(entries, output_path)
    stat_report(entries)
    print(f"[build] Encrypted: {size:,} bytes -> {output_path}")
    print(f"[build] Total entries: {len(entries)}")
    return output_path


# ============================================================
# 辅助函数
# ============================================================


def _find_data_file(name: str) -> Optional[str]:
    """查找数据文件。"""
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "..", "data", name),
        os.path.join(os.path.dirname(__file__), "..", "data", name),
        name,
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _find_or_load_key_store(path: Optional[str] = None) -> list[dict]:
    """查找或加载 key-store.json。"""
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    found = _find_data_file("key-store-v3.19.4.json")
    if found:
        with open(found, "r", encoding="utf-8") as f:
            return json.load(f)
    # 从 examples 找
    examples = os.path.join(os.path.dirname(__file__), "..", "..", "examples", "key-store.json")
    if os.path.exists(examples):
        with open(examples, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _find_or_load_record_map(path: Optional[str] = None) -> list[dict]:
    """查找或加载 record-key-map.json。"""
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    found = _find_data_file("record-key-map-v3.19.4.json")
    if found:
        with open(found, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# ============================================================
# CLI 入口
# ============================================================


def main():
    parser = argparse.ArgumentParser(
        prog="phigros-save",
        description="Phigros v3.19.4 存档管理工具 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 零配置生成全满分全解锁存档
  %(prog)s build-full output.xml --rank 551

  # 以现有存档为基线
  %(prog)s build-from my_save.xml output.xml --rank 551

  # 配置文件法（精确控制）
  %(prog)s build-config ./config/ output.xml

  # 拆包 APK
  %(prog)s unpack Phigros.apk ./extracted

  # 加解密
  %(prog)s decrypt playerprefs.xml data.json
  %(prog)s encrypt data.json playerprefs.xml
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # --- unpack ---
    unpack_p = subparsers.add_parser("unpack", help="Extract song data from APK")
    unpack_p.add_argument("apk_path", help="APK file path")
    unpack_p.add_argument("output_dir", help="Output directory")

    # --- decrypt ---
    decrypt_p = subparsers.add_parser("decrypt", help="Decrypt playerprefs.xml to JSON")
    decrypt_p.add_argument("input", help="Input XML file")
    decrypt_p.add_argument("output", help="Output JSON file")
    decrypt_p.add_argument("--new-key", action="store_true", help="Use new derived key")

    # --- encrypt ---
    encrypt_p = subparsers.add_parser("encrypt", help="Encrypt JSON to playerprefs.xml")
    encrypt_p.add_argument("input", help="Input JSON file")
    encrypt_p.add_argument("output", help="Output XML file")
    encrypt_p.add_argument("--new-key", action="store_true", help="Use new derived key")

    # --- build-full ---
    build_full_p = subparsers.add_parser(
        "build-full",
        help="Zero-config: generate full-unlock save in one line",
    )
    build_full_p.add_argument("output", help="Output XML file")
    build_full_p.add_argument("--rank", default="551", help="ChallengeModeRank (default: 551=彩51)")
    build_full_p.add_argument("--game-completed", default="3.0", help="GameCompleted value")
    build_full_p.add_argument("--player-name", help="Player name")
    build_full_p.add_argument("--baseline", help="Baseline XML (keep config, replace records)")
    build_full_p.add_argument("--key-store", help="key-store.json path")
    build_full_p.add_argument("--record-map", help="record-key-map.json path")

    # --- build-from ---
    build_from_p = subparsers.add_parser(
        "build-from",
        help="Modify existing save: add full scores and unlock",
    )
    build_from_p.add_argument("baseline", help="Baseline XML file")
    build_from_p.add_argument("output", help="Output XML file")
    build_from_p.add_argument("--rank", help="ChallengeModeRank")
    build_from_p.add_argument("--game-completed", help="GameCompleted value")
    build_from_p.add_argument("--player-name", help="Player name")
    build_from_p.add_argument("--key-store", help="key-store.json path")
    build_from_p.add_argument("--record-map", help="record-key-map.json path")

    # --- build-config ---
    build_config_p = subparsers.add_parser(
        "build-config",
        help="Build from config directory (songs.json + key-store.json + settings.json)",
    )
    build_config_p.add_argument("config_dir", help="Config directory")
    build_config_p.add_argument("output", help="Output XML file")
    build_config_p.add_argument("--rank", default="551", help="ChallengeModeRank")
    build_config_p.add_argument("--game-completed", default="3.0", help="GameCompleted value")

    args = parser.parse_args()

    if args.command == "unpack":
        unpack_apk(args.apk_path, args.output_dir)

    elif args.command == "decrypt":
        key = Keys.ZIP_KEY if args.new_key else Keys.OLD_KEY
        iv = Keys.ZIP_IV if args.new_key else Keys.OLD_IV
        entries, failed = decrypt_playerprefs_xml(args.input, key, iv)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"[decrypt] Decrypted: {len(entries)} entries")
        stat_report(entries)
        if failed:
            print(f"[decrypt] Failed: {len(failed)} keys")

    elif args.command == "encrypt":
        with open(args.input, "r", encoding="utf-8") as f:
            entries = json.load(f)
        key = Keys.ZIP_KEY if args.new_key else Keys.OLD_KEY
        iv = Keys.ZIP_IV if args.new_key else Keys.OLD_IV
        size = encrypt_to_playerprefs_xml(entries, args.output, key, iv)
        print(f"[encrypt] Encrypted: {size:,} bytes")

    elif args.command == "build-full":
        build_full_save(
            args.output,
            rank=args.rank,
            game_completed=args.game_completed,
            player_name=args.player_name,
            key_store_path=args.key_store,
            record_map_path=args.record_map,
            baseline_path=args.baseline,
        )

    elif args.command == "build-from":
        build_from_baseline(
            args.baseline,
            args.output,
            rank=args.rank,
            game_completed=args.game_completed,
            player_name=args.player_name,
            key_store_path=args.key_store,
            record_map_path=args.record_map,
        )

    elif args.command == "build-config":
        build_custom_save(
            args.config_dir,
            args.output,
            challenge_rank=args.rank,
            game_completed=args.game_completed,
        )

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()