"""测试加密/解密 roundtrip。"""

import json
import tempfile
from pathlib import Path

from phigros_save_tool.crypto import (
    Keys,
    decrypt_playerprefs_xml,
    encrypt_to_playerprefs_xml,
)


def test_encrypt_decrypt_roundtrip():
    """加密后解密应完全还原。"""
    entries = {
        "Introduction.Record.EZ": '{"s":1000000,"a":100.0,"c":2}',
        "0keyDer Schneid": "1",
        "1keyTest": "1",
        "GameCompleted": "3.0",
        "playerName": "TestPlayer",
    }

    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "test.xml"
        encrypt_to_playerprefs_xml(entries, str(xml_path))

        verified, failed = decrypt_playerprefs_xml(str(xml_path))
        assert len(failed) == 0, f"Failed to decrypt: {failed}"
        assert len(verified) == len(entries), (
            f"Mismatch: {len(verified)} vs {len(entries)}"
        )
        for k, v in entries.items():
            assert verified[k] == v, f"Mismatch for {k}: {verified[k]} != {v}"


def test_special_characters():
    """含中文和特殊字符的键值对应正确加解密。"""
    entries = {
        "0key狂喜蘭舞": "1",
        "Introduction.Record.EZ": '{"s":1000000,"a":100.0,"c":2}',
        "playerName": "测试玩家🎵",
        "selfIntro": "Line1\r\nLine2\r\n",
    }

    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "special.xml"
        encrypt_to_playerprefs_xml(entries, str(xml_path))

        verified, failed = decrypt_playerprefs_xml(str(xml_path))
        assert len(failed) == 0
        for k, v in entries.items():
            assert verified[k] == v, f"Mismatch for {k}: {repr(verified[k])} != {repr(v)}"


def test_empty_values():
    """空值应能正确处理。"""
    entries = {
        "playerName": "",
        "selfIntro": "",
        "KeyWithValue": "some value",
    }

    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "empty.xml"
        encrypt_to_playerprefs_xml(entries, str(xml_path))

        verified, failed = decrypt_playerprefs_xml(str(xml_path))
        assert len(failed) == 0
        assert verified["playerName"] == ""
        assert verified["selfIntro"] == ""
        assert verified["KeyWithValue"] == "some value"


def test_key_constants():
    """密钥常量应可正确初始化。"""
    assert len(Keys.OLD_KEY) == 32, "OLD_KEY should be 32 bytes"
    assert len(Keys.OLD_IV) == 16, "OLD_IV should be 16 bytes"
    assert len(Keys.ZIP_KEY) == 32, "ZIP_KEY should be 32 bytes"
    assert len(Keys.ZIP_IV) == 16, "ZIP_IV should be 16 bytes"


if __name__ == "__main__":
    test_encrypt_decrypt_roundtrip()
    test_special_characters()
    test_empty_values()
    test_key_constants()
    print("All tests passed!")
