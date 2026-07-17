"""版本拆包模块。

从 APK 中提取 catalog.json、songs.json、key-store.json、谱面 bundle 清单等。
"""

import json
import os
import zipfile
from pathlib import Path


def unpack_apk(apk_path: str, output_dir: str) -> None:
    """从 APK 拆包歌曲数据。

    Args:
        apk_path: APK 文件路径
        output_dir: 输出目录

    Output files:
        catalog.json            — Addressables 目录
        songs_from_catalog.json — 解析后的歌曲列表
        songs.json              — 歌曲信息
        key-store.json          — 解锁键配置
        bundle_manifest.json    — 谱面资源清单
    """
    apk_path = str(Path(apk_path).resolve())
    output_dir = str(Path(output_dir).resolve())
    os.makedirs(output_dir, exist_ok=True)

    extracted: list[tuple[str, int]] = []

    with zipfile.ZipFile(apk_path, "r") as zf:
        namelist = zf.namelist()

        # 1. catalog.json
        for cf in namelist:
            if "catalog.json" in cf.lower():
                data = zf.read(cf)
                out_name = os.path.basename(cf)
                out_path = os.path.join(output_dir, out_name)
                with open(out_path, "wb") as f:
                    f.write(data)
                extracted.append((out_name, len(data)))

                # 解析歌曲列表
                try:
                    catalog = json.loads(data)
                    songs = []
                    if isinstance(catalog, dict) and "groups" in catalog:
                        for group in catalog["groups"]:
                            for entry in group.get("entries", []):
                                songs.append({
                                    "resource_id": entry.get("addressable_name", ""),
                                    "path": entry.get("address", ""),
                                    "group": group.get("group_name", ""),
                                })
                    elif isinstance(catalog, list):
                        for entry in catalog:
                            songs.append({
                                "resource_id": entry.get("addressable_name", ""),
                                "path": entry.get("address", ""),
                            })

                    if songs:
                        song_path = os.path.join(output_dir, "songs_from_catalog.json")
                        with open(song_path, "w", encoding="utf-8") as f:
                            json.dump(songs, f, ensure_ascii=False, indent=2)
                        extracted.append(("songs_from_catalog.json", len(songs)))
                except Exception as e:
                    print(f"[warn] Failed to parse catalog {cf}: {e}")

        # 2. songs.json / logical-songs.json
        for sf in namelist:
            if sf.endswith(".json") and "song" in sf.lower():
                data = zf.read(sf)
                out_name = os.path.basename(sf)
                out_path = os.path.join(output_dir, out_name)
                with open(out_path, "wb") as f:
                    f.write(data)
                extracted.append((out_name, len(data)))

        # 3. key-store / keyStore
        for kf in namelist:
            if "keystore" in kf.lower() or "key_store" in kf.lower():
                data = zf.read(kf)
                out_name = os.path.basename(kf)
                out_path = os.path.join(output_dir, out_name)
                with open(out_path, "wb") as f:
                    f.write(data)
                extracted.append((out_name, len(data)))

        # 4. bundle 清单
        bundles = [n for n in namelist if n.endswith(".bundle")]
        bundle_info = []
        for bf in bundles[:50]:
            size = zf.getinfo(bf).file_size
            bundle_info.append({"path": bf, "size": size})
        bundle_info.append({"total": len(bundles)})

        bm_path = os.path.join(output_dir, "bundle_manifest.json")
        with open(bm_path, "w", encoding="utf-8") as f:
            json.dump(bundle_info, f, ensure_ascii=False, indent=2)
        extracted.append(("bundle_manifest.json", os.path.getsize(bm_path)))

    print(f"\n[unpack] Extracted {len(extracted)} files to {output_dir}:")
    for name, size in extracted:
        print(f"  {name:<40s} {size:>10,} bytes")
