"""Phigros 版本数据管理器。

支持多版本数据切换，内置 v3.19.4 完整数据。
"""

import json
from pathlib import Path
from typing import Optional


class VersionManager:
    """版本数据管理器。"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.current_version = None
        self._load_versions()

    def _load_versions(self):
        """扫描可用版本。"""
        self.versions = {}
        if self.data_dir.exists():
            for f in self.data_dir.glob("*.json"):
                name = f.stem
                # 只处理带 -v 后缀的版本文件
                if "-v" in name:
                    version = name.split("-v")[-1]
                    if version not in self.versions:
                        self.versions[version] = []
                    self.versions[version].append(f.name)

    def list_versions(self) -> list[str]:
        """列出所有可用版本。"""
        return sorted(self.versions.keys())

    def use_version(self, version: str) -> bool:
        """切换到指定版本。"""
        if version not in self.versions:
            print(f"[error] Version {version} not found")
            return False
        self.current_version = version
        return True

    def get_data_files(self, version: Optional[str] = None) -> dict[str, str]:
        """获取指定版本的数据文件路径。"""
        version = version or self.current_version
        if not version:
            raise ValueError("No version selected")
        result = {}
        for filename in self.versions.get(version, []):
            filepath = self.data_dir / filename
            result[filename] = str(filepath)
        return result

    def load_key_store(self, version: Optional[str] = None) -> list[dict]:
        """加载 key-store 数据。"""
        files = self.get_data_files(version)
        key_file = next((f for f in files if "key-store" in f), None)
        if not key_file:
            return []
        with open(files[key_file], "r", encoding="utf-8") as f:
            return json.load(f)

    def load_record_map(self, version: Optional[str] = None) -> list[dict]:
        """加载 record-key-map 数据。"""
        files = self.get_data_files(version)
        map_file = next((f for f in files if "record-key-map" in f), None)
        if not map_file:
            return []
        with open(files[map_file], "r", encoding="utf-8") as f:
            return json.load(f)

    def load_songs(self, version: Optional[str] = None) -> list[dict]:
        """加载 songs 数据。"""
        files = self.get_data_files(version)
        songs_file = next((f for f in files if "songs" in f), None)
        if not songs_file:
            return []
        with open(files[songs_file], "r", encoding="utf-8") as f:
            return json.load(f)

    def get_current_version_info(self) -> dict:
        """获取当前版本信息。"""
        if not self.current_version:
            return {"version": None, "files": []}
        files = self.get_data_files(self.current_version)
        return {
            "version": self.current_version,
            "files": list(files.keys()),
        }

    def get_version_info(self, version: str) -> dict:
        """获取指定版本信息。"""
        if version not in self.versions:
            return {"version": version, "files": []}
        files = self.get_data_files(version)
        return {
            "version": version,
            "files": list(files.keys()),
        }


def create_default_manager(data_dir: str) -> VersionManager:
    """创建默认版本管理器，自动选择最新版本。"""
    manager = VersionManager(data_dir)
    versions = manager.list_versions()
    if versions:
        manager.use_version(versions[-1])
    return manager
