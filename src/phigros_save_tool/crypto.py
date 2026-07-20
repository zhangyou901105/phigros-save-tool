"""加密工具模块

AES-256-CBC 加解密、Base64/URL 编码、LoopReverseXor 密钥派生。
"""

import base64
import json
import os
import urllib.parse
from pathlib import Path
from typing import Optional

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class Keys:
    """Phigros v3.19.4 所有加密密钥。

    PlayerPrefs XML 使用旧 KEY/IV（完整存档 / 1.zip 同源）。
    ZIP 五模块使用独立 Base64 派生密钥。
    """

    # --- PlayerPrefs 旧 KEY/IV ---
    OLD_KEY = bytes.fromhex(
        "627ff1942185e011c815e81e639b9a00"
        "001c766b826c29bd96578589f19a6fd6"
    )
    OLD_IV = bytes.fromhex("be56167f83da3befeff81861a5c5f3cd")

    # --- ZIP 五模块 KEY/IV ---
    ZIP_KEY = base64.b64decode("6Jaa0qVAJZuXkZCLiOa/Ax5tIZVu+taKUN1V1nqwkks=")
    ZIP_IV = base64.b64decode("Kk/wisgNYwcAV8WVGMgyUw==")


# ============================================================
# 位操作 & LoopReverseXor
# ============================================================


def reverse_bits(x: int) -> int:
    """8-bit 位反转。"""
    x = ((x & 0x55) << 1) | ((x >> 1) & 0x55)
    x = ((x & 0x33) << 2) | ((x >> 2) & 0x33)
    x = ((x & 0x0F) << 4) | ((x >> 4) & 0x0F)
    return x


def loop_reverse_xor(key_bytes: bytes, iv_bytes: bytes) -> bytes:
    """LoopReverseXor 密钥派生算法。"""
    result = bytearray()
    for i in range(len(key_bytes)):
        byte = reverse_bits(key_bytes[i]) ^ iv_bytes[i % len(iv_bytes)]
        result.append(byte)
    return bytes(result)


# ============================================================
# Base64 / URL 编解码
# ============================================================


def url_b64_decode(text: str) -> bytes:
    """URL 编码的 Base64 解码。"""
    s = urllib.parse.unquote(text or "")
    return base64.b64decode(s + "=" * ((-len(s)) % 4))


def url_b64_encode(raw_bytes: bytes) -> str:
    """Base64 编码 + URL 编码。"""
    return urllib.parse.quote(base64.b64encode(raw_bytes).decode("ascii"), safe="")


# ============================================================
# 单字段加解密
# ============================================================


def decrypt_text(text: str, key: bytes, iv: bytes) -> Optional[str]:
    """解密单个文本字段。失败返回 None。"""
    try:
        raw = url_b64_decode(text)
        if not raw or len(raw) % 16:
            return None
        return unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(raw), 16).decode("utf-8")
    except Exception:
        return None


def encrypt_text(text: str, key: bytes, iv: bytes) -> str:
    """加密单个文本字段。"""
    raw = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(text.encode("utf-8"), 16))
    return url_b64_encode(raw)


# ============================================================
# 整个 playerprefs.xml 加解密
# ============================================================


def decrypt_playerprefs_xml(
    xml_path: str, key: Optional[bytes] = None, iv: Optional[bytes] = None
) -> tuple[dict[str, str], list[str]]:
    """解密 playerprefs.xml → (entries_dict, failed_keys)。

    Returns:
        entries: {明文键名: 明文值} 字典
        failed: 无法解密的原始 name 属性前 40 字符列表
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(xml_path)
    root = tree.getroot()

    if key is None:
        key = Keys.OLD_KEY
    if iv is None:
        iv = Keys.OLD_IV

    entries: dict[str, str] = {}
    failed: list[str] = []

    for elem in root.findall("string"):
        enc_name = elem.get("name", "")
        enc_value = elem.text or ""

        name = decrypt_text(enc_name, key, iv)
        if name is None:
            failed.append(enc_name[:40])
            continue

        value = decrypt_text(enc_value, key, iv)
        entries[name] = value if value else ""

    return entries, failed


def encrypt_to_playerprefs_xml(
    entries: dict[str, str],
    xml_path: str,
    key: Optional[bytes] = None,
    iv: Optional[bytes] = None,
) -> int:
    """将 entries 字典加密写入 playerprefs.xml。

    Returns:
        输出文件大小（字节）
    """
    import xml.etree.ElementTree as ET

    if key is None:
        key = Keys.OLD_KEY
    if iv is None:
        iv = Keys.OLD_IV

    root = ET.Element("map")
    for name in sorted(entries.keys()):
        value = entries[name]
        enc_name = encrypt_text(name, key, iv)
        enc_value = encrypt_text(value, key, iv)
        elem = ET.SubElement(root, "string", {"name": enc_name})
        elem.text = enc_value

    tree = ET.ElementTree(root)
    with open(xml_path, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    return os.path.getsize(xml_path)
