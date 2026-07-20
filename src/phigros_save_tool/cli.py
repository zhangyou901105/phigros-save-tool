"""CLI 命令行入口。

支持三种 build 模式 + 版本切换:
  phigros-save build-full output.xml --version 3.19.4
  phigros-save build-from baseline.xml output.xml --version 3.19.4
  phigros-save list-versions
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
from .version_manager import VersionManager


# ============================================================
# 零配置全存档构建
# ============================================================

def _get_project_data_dir() -> Path:
    """查找项目 data/ 目录（开发+打包模式）。"""
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "data",
        Path(__file__).resolve().parent.parent / "data",
        Path.cwd() / "data",
    ]
    if getattr(sys, 'frozen', False):
        candidates.insert(0, Path(sys._MEIPASS) / "data")
    for c in candidates:
        if c.exists():
            return c
    return Path.cwd() / "data"


def build_full_save(
    output_path: str,
    rank: str = "551",
    game_completed: str = "3.0",
    player_name: Optional[str] = None,
    key_store_path: Optional[str] = None,
    record_map_path: Optional[str] = None,
    baseline_path: Optional[str] = None,
    data_version: Optional[str] = None,
    data_dir: Optional[str] = None,
) -> str:
    """一行命令生成全满分全解锁存档。"""
    output_path = str(Path(output_path).resolve())

    # 版本管理器
    vm = VersionManager(data_dir or str(_get_project_data_dir()))
    if data_version:
        vm.use_version(data_version)
    elif not vm.current_version and vm.list_versions():
        vm.use_version(vm.list_versions()[-1])

    # 加载 key-store / record-map
    if key_store_path:
        with open(key_store_path, "r", encoding="utf-8") as f:
            key_store = json.load(f)
    else:
        key_store = vm.load_key_store()

    if record_map_path:
        with open(record_map_path, "r", encoding="utf-8") as f:
            record_map = json.load(f)
    else:
        record_map = vm.load_record_map()

    print(f"[info] Key-store: {len(key_store)} keys loaded")
    print(f"[info] Record map: {len(record_map)} records")

    # 基线存档
    baseline_entries: dict[str, str] = {}
    if baseline_path and os.path.exists(baseline_path):
        baseline_entries, _ = decrypt_playerprefs_xml(baseline_path)
        print(f"[info] Baseline: {len(baseline_entries)} entries loaded")

    # 构建
    entries: dict[str, str] = {}

    if baseline_entries:
        for k, v in baseline_entries.items():
            if not k.startswith(("0key", "1key", "2key", "3key")) and not ".Record." in k:
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
        if kind == 0:
            entries[key] = str(target_count)
        elif kind == 1:
            entries[key] = str(target_count)
        elif kind == 2:
            entries[key] = "1"
        elif kind == 3:
            entries[key] = "1"

    # --- CollectionTextOpened ---
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
        "C8CraveWaveUnlocked", "C8DESTRUCTION321Unlocked", "C8DistortedFateUnlocked",
        "C8LuminescenceUnlocked", "C8RetributionUnlocked", "C8TheChariotREVIIVALUnlocked",
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

    size = encrypt_to_playerprefs_xml(entries, output_path)
    stat_report(entries)
    ver_info = vm.get_current_version_info()
    print(f"[build] Encrypted: {size:,} bytes -> {output_path}")
    print(f"[build] Total entries: {len(entries)} | Version: {ver_info['version']}")
    return output_path


def stat_report(entries: dict[str, str]) -> None:
    """打印存档统计。"""
    record_count = sum(1 for k in entries if ".Record." in k)
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
    data_version: Optional[str] = None,
    data_dir: Optional[str] = None,
) -> str:
    """以现有存档为基线，修改部分内容。"""
    output_path = str(Path(output_path).resolve())

    baseline_entries, failed = decrypt_playerprefs_xml(baseline_path)
    print(f"[info] Baseline: {len(baseline_entries)} entries ({len(failed)} failed)")

    vm = VersionManager(data_dir or str(_get_project_data_dir()))
    if data_version:
        vm.use_version(data_version)
    elif not vm.current_version and vm.list_versions():
        vm.use_version(vm.list_versions()[-1])

    if key_store_path:
        with open(key_store_path, "r", encoding="utf-8") as f:
            key_store = json.load(f)
    else:
        key_store = vm.load_key_store()

    if record_map_path:
        with open(record_map_path, "r", encoding="utf-8") as f:
            record_map = json.load(f)
    else:
        record_map = vm.load_record_map()

    entries = dict(baseline_entries)

    FULL_SCORE = json.dumps({"s": 1000000, "a": 100.0, "c": 2}, separators=(",", ":"))
    for rm in record_map:
        key = rm["playerprefs_key"]
        if key not in entries:
            entries[key] = FULL_SCORE

    for sk in key_store:
        key = sk["playerprefs_key"]
        kind = sk.get("kind", 0)
        target_count = sk.get("target_count", 1)
        if key not in entries:
            entries[key] = str(target_count)

    for sk in key_store:
        if sk.get("kind") == 1:
            key = sk["playerprefs_key"]
            tc = sk.get("target_count", 1)
            ct_key = key.replace("1key", "") + "CollectionTextOpened"
            if ct_key not in entries:
                entries[ct_key] = str(max(tc, 2))

    if rank is not None:
        entries["challengeModeRank"] = rank
    if game_completed is not None:
        entries["GameCompleted"] = game_completed
    if player_name is not None:
        entries["playerName"] = player_name

    size = encrypt_to_playerprefs_xml(entries, output_path)
    stat_report(entries)
    print(f"[build] Encrypted: {size:,} bytes -> {output_path}")
    print(f"[build] Total entries: {len(entries)} | Version: {vm.current_version}")
    return output_path


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog="phigros-save",
        description="Phigros 存档管理工具 v2.1 — 内置版本数据，支持版本切换",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 列出可用版本
  %(prog)s list-versions

  # 零配置生成（自动使用最新内置版本）
  %(prog)s build-full output.xml --rank 551

  # 指定版本
  %(prog)s build-full output.xml --version 3.19.4

  # 以现有存档为基线
  %(prog)s build-from my_save.xml output.xml --version 3.19.4

  # 拆包 APK
  %(prog)s unpack Phigros.apk ./extracted
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # --- list-versions ---
    subparsers.add_parser("list-versions", help="List available built-in versions")

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
    build_full_p.add_argument("--key-store", help="key-store.json path (overrides built-in)")
    build_full_p.add_argument("--record-map", help="record-key-map.json path (overrides built-in)")
    build_full_p.add_argument("--version", help="Version to use (e.g. 3.19.4)")

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
    build_from_p.add_argument("--key-store", help="key-store.json path (overrides built-in)")
    build_from_p.add_argument("--record-map", help="record-key-map.json path (overrides built-in)")
    build_from_p.add_argument("--version", help="Version to use (e.g. 3.19.4)")

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

    if args.command == "list-versions":
        data_dir = _get_project_data_dir()
        vm = VersionManager(str(data_dir))
        versions = vm.list_versions()
        if versions:
            print(f"Available versions: {', '.join(versions)}")
            for v in versions:
                info = vm.get_version_info(v)
                print(f"  {v}: {', '.join(info['files'])}")
        else:
            print("No versions found in data/")
        return

    elif args.command == "unpack":
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
            data_version=args.version,
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
            data_version=args.version,
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
