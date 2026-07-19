#!/usr/bin/env python3
"""Phigros Save Manager GUI 启动器。

用法:
  python run_gui.py
  python run_gui.py --file path/to/save.xml   # 打开指定存档
"""

import sys
import tkinter as tk
from pathlib import Path

# 确保能找到本地包
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from phigros_save_tool.gui import PhigrosSaveEditor


def main():
    root = tk.Tk()

    # 如果传入了存档路径参数，自动加载
    if len(sys.argv) > 1:
        from phigros_save_tool.crypto import decrypt_playerprefs_xml

        app = PhigrosSaveEditor(root)
        try:
            entries, failed = decrypt_playerprefs_xml(sys.argv[1])
            app.entries = entries
            app.current_file = sys.argv[1]
            app.refresh_entries()
            app.update_stats()
            app.status_var.set(f"已加载：{sys.argv[1]}")
        except Exception as e:
            print(f"加载失败：{e}")

        root.mainloop()
    else:
        app = PhigrosSaveEditor(root)
        root.mainloop()


if __name__ == "__main__":
    main()
