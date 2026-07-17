"""CLI 命令行入口。

用法:
  phigros-save unpack <apk> <output_dir>
  phigros-save decrypt <input.xml> <output.json>
  phigros-save encrypt <input.json> <output.xml>
  phigros-save build <config_dir> <output.xml> [--rank RANK] [--game-completed VAL]
"""

import argparse
import sys
from pathlib import Path

from .crypto import Keys, decrypt_playerprefs_xml, encrypt_to_playerprefs_xml
from .unpack import unpack_apk
from .build import build_custom_save


def main():
    parser = argparse.ArgumentParser(
        prog="phigros-save",
        description="Phigros v3.19.4 存档管理工具 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 从 APK 拆包歌曲数据
  %(prog)s unpack Phigros-v3.19.4.apk ./extracted

  # 解密存档
  %(prog)s decrypt com.PigeonGames.Phigros.v2.playerprefs.xml savedata.json

  # 加密存档
  %(prog)s encrypt savedata.json output.xml

  # 构建自定义存档（彩色51级）
  %(prog)s build ./my-config/ output.xml --rank 551
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # unpack
    unpack_p = subparsers.add_parser("unpack", help="Extract song data from APK")
    unpack_p.add_argument("apk_path", help="APK file path")
    unpack_p.add_argument("output_dir", help="Output directory")

    # decrypt
    decrypt_p = subparsers.add_parser("decrypt", help="Decrypt playerprefs.xml to JSON")
    decrypt_p.add_argument("input", help="Input XML file")
    decrypt_p.add_argument("output", help="Output JSON file")
    decrypt_p.add_argument("--new-key", action="store_true", help="Use new derived key")

    # encrypt
    encrypt_p = subparsers.add_parser("encrypt", help="Encrypt JSON to playerprefs.xml")
    encrypt_p.add_argument("input", help="Input JSON file")
    encrypt_p.add_argument("output", help="Output XML file")
    encrypt_p.add_argument("--new-key", action="store_true", help="Use new derived key")

    # build
    build_p = subparsers.add_parser("build", help="Build custom save from config")
    build_p.add_argument("config_dir", help="Config directory")
    build_p.add_argument("output", help="Output XML file")
    build_p.add_argument("--rank", default="551", help="ChallengeModeRank (default: 551)")
    build_p.add_argument("--game-completed", default="3.0", help="GameCompleted value")

    args = parser.parse_args()

    if args.command == "unpack":
        unpack_apk(args.apk_path, args.output_dir)

    elif args.command == "decrypt":
        key = Keys.ZIP_KEY if args.new_key else Keys.OLD_KEY
        iv = Keys.ZIP_IV if args.new_key else Keys.OLD_IV
        entries, failed = decrypt_playerprefs_xml(args.input, key, iv)

        with open(args.output, "w", encoding="utf-8") as f:
            import json

            json.dump(entries, f, ensure_ascii=False, indent=2)

        print(f"[decrypt] Decrypted: {len(entries)} entries")
        if failed:
            print(f"[decrypt] Failed: {len(failed)} keys")

    elif args.command == "encrypt":
        import json

        with open(args.input, "r", encoding="utf-8") as f:
            entries = json.load(f)

        key = Keys.ZIP_KEY if args.new_key else Keys.OLD_KEY
        iv = Keys.ZIP_IV if args.new_key else Keys.OLD_IV
        size = encrypt_to_playerprefs_xml(entries, args.output, key, iv)
        print(f"[encrypt] Encrypted: {size:,} bytes")

    elif args.command == "build":
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
