"""测试 build_custom_save。"""

import json
import tempfile
from pathlib import Path

from phigros_save_tool.build import build_custom_save


def test_build_basic():
    """基础构建应产生正确数量的条目。"""
    with tempfile.TemporaryDirectory() as tmp:
        config_dir = Path(tmp) / "config"
        config_dir.mkdir()

        # 创建最小配置
        songs = [{"name": "Glaciaxion", "variant": "EZ", "score": 1000000}]
        (config_dir / "songs.json").write_text(json.dumps(songs))

        key_store = [
            {"playerprefs_key": "0keyGlaciaxion", "kind": 0, "target_count": 1},
        ]
        (config_dir / "key-store.json").write_text(json.dumps(key_store))

        output = Path(tmp) / "output.xml"
        entries = build_custom_save(str(config_dir), str(output))

        assert "GameCompleted" in entries
        assert entries["GameCompleted"] == "3.0"
        assert "0keyGlaciaxion" in entries
        assert entries["0keyGlaciaxion"] == "1"


def test_build_challenge_rank():
    """ChallengeModeRank 应可自定义。"""
    with tempfile.TemporaryDirectory() as tmp:
        config_dir = Path(tmp) / "config"
        config_dir.mkdir()
        (config_dir / "songs.json").write_text("[]")
        (config_dir / "key-store.json").write_text("[]")

        output = Path(tmp) / "output.xml"
        entries = build_custom_save(
            str(config_dir), str(output), challenge_rank="499"
        )

        assert entries["challengeModeRank"] == "499"


def test_build_game_completed():
    """GameCompleted 应可自定义。"""
    with tempfile.TemporaryDirectory() as tmp:
        config_dir = Path(tmp) / "config"
        config_dir.mkdir()
        (config_dir / "songs.json").write_text("[]")
        (config_dir / "key-store.json").write_text("[]")

        output = Path(tmp) / "output.xml"
        entries = build_custom_save(
            str(config_dir), str(output), game_completed="2.0"
        )

        assert entries["GameCompleted"] == "2.0"


if __name__ == "__main__":
    test_build_basic()
    test_build_challenge_rank()
    test_build_game_completed()
    print("All build tests passed!")
