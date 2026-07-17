"""Phigros Save Manager v2.0

完整存档管理工具，支持：
- APK 版本拆包（提取歌曲目录、key-store、谱面清单）
- 存档解密（加密 XML → 可读 JSON）
- 存档加密（可读 JSON → 加密 XML）
- 自定义存档构建（根据配置文件夹生成完整加密存档）

密钥来源：Phigros v3.19.4 逆向工程（Il2CppDumper + ARM64 控制流分析）
"""

from .crypto import Keys, decrypt_text, encrypt_text, decrypt_playerprefs_xml, encrypt_to_playerprefs_xml
from .unpack import unpack_apk
from .build import build_custom_save

__all__ = [
    "Keys",
    "decrypt_text",
    "encrypt_text",
    "decrypt_playerprefs_xml",
    "encrypt_to_playerprefs_xml",
    "unpack_apk",
    "build_custom_save",
]
__version__ = "2.0.0"
