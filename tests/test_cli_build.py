"""测试 build-full 和 build-from CLI 模式。"""

import json
import tempfile
from pathlib import Path

from phigros_save_tool.cli import build_full_save, build_from_baseline


def test_build_full_zero_config():
    """零配置生成存档。"""
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "output.xml"
        path = build_full_save(
            str(output), rank="232", game_completed="3.0", player_name="Test"
        )
        assert output.exists()
        assert output.stat().st_size > 0


def test_build_from_baseline():
    """基线法生成存档。"""
    with tempfile.TemporaryDirectory() as tmp:
        # 创建基线
        baseline = Path(tmp) / "baseline.xml"
        from phigros_save_tool.crypto import encrypt_to_playerprefs_xml
        entries = {
            "Introduction.Record.EZ": '{"s":933295,"a":97.06,"c":0}',
            "0keyDer Schneid": "1",
            "1keyTest1": "3",
            "playerName": "OrigPlayer",
            "GameCompleted": "2.0",
            "challengeModeRank": "100",
        }
        encrypt_to_playerprefs_xml(entries, str(baseline))

        # build-from
        output = Path(tmp) / "output.xml"
        path = build_from_baseline(
            str(baseline), str(output), rank="551", player_name="NewName"
        )

        # 验证
        from phigros_save_tool.crypto import decrypt_playerprefs_xml
        decrypted, failed = decrypt_playerprefs_xml(str(output))
        assert len(failed) == 0
        assert decrypted.get("challengeModeRank") == "551"
        assert decrypted.get("playerName") == "NewName"
        assert decrypted.get("GameCompleted") == "2.0"  # 未覆盖，保留基线
        assert decrypted.get("0keyDer Schneid") == "1"
        assert decrypted.get("1keyTest1") == "3"


def test_build_from_baseline_keep_existing_records():
    """基线法不覆盖已有成绩。"""
    with tempfile.TemporaryDirectory() as tmp:
        baseline = Path(tmp) / "baseline.xml"
        from phigros_save_tool.crypto import encrypt_to_playerprefs_xml
        existing = '{"s":888888,"a":99.0,"c":1}'
        entries = {"Introduction.Record.EZ": existing}
        encrypt_to_playerprefs_xml(entries, str(baseline))

        output = Path(tmp) / "output.xml"
        build_from_baseline(str(baseline), str(output), rank="551")

        from phigros_save_tool.crypto import decrypt_playerprefs_xml
        decrypted, failed = decrypt_playerprefs_xml(str(output))
        assert len(failed) == 0
        # 已有成绩保留
        assert decrypted["Introduction.Record.EZ"] == existing


def test_build_full_with_baseline():
    """build-full --baseline 模式。"""
    with tempfile.TemporaryDirectory() as tmp:
        baseline = Path(tmp) / "baseline.xml"
        from phigros_save_tool.crypto import encrypt_to_playerprefs_xml
        entries = {
            "playerName": "BaselinePlayer",
            "musicVolume": "0.8",
        }
        encrypt_to_playerprefs_xml(entries, str(baseline))

        output = Path(tmp) / "output.xml"
        path = build_full_save(
            str(output), rank="551", baseline_path=str(baseline)
        )

        from phigros_save_tool.crypto import decrypt_playerprefs_xml
        decrypted, _ = decrypt_playerprefs_xml(str(output))
        # 基线设置被保留
        assert decrypted.get("playerName") == "BaselinePlayer"
        assert decrypted.get("musicVolume") == "0.8"
        # 新值覆盖
        assert decrypted.get("challengeModeRank") == "551"


if __name__ == "__main__":
    test_build_full_zero_config()
    test_build_from_baseline()
    test_build_from_baseline_keep_existing_records()
    test_build_full_with_baseline()
    print("All CLI build tests passed!")