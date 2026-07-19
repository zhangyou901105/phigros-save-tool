"""Phigros Save Manager GUI 启动器。

用法:
  python run_gui.py
  python run_gui.py path/to/save.xml   # 打开指定存档

PyInstaller 打包:
  pyinstaller --onefile --name PhigrosSaveManager --add-data "src;src" run_gui.py
"""

import sys
import os
import tkinter as tk
from pathlib import Path

# PyInstaller --onefile 模式下 __file__ 不可用，使用 sys._MEIPASS
if getattr(sys, 'frozen', False):
    base = Path(sys._MEIPASS) / "src"
else:
    base = Path(__file__).resolve().parent / "src"

sys.path.insert(0, str(base))


def main():
    try:
        from phigros_save_tool.gui import PhigrosSaveEditor
    except ImportError as e:
        # Auto-relaunch with Python 3.13 if pycryptodome missing
        if "Crypto" in str(e):
            candidates = [
                r"C:\Users\Arlec\AppData\Local\Programs\Python\Python313\python.exe",
                r"C:\Python313\python.exe",
            ]
            for py in candidates:
                if os.path.exists(py):
                    print(f"Relaunching with {py}...")
                    os.execv(py, [py, __file__] + sys.argv[1:])
            print(f"\nError: {e}")
            print("Install pycryptodome: pip install pycryptodome")
            input("\nPress Enter to exit...")
            return
        raise

    root = tk.Tk()
    app = PhigrosSaveEditor(root)

    if len(sys.argv) > 1:
        from phigros_save_tool.crypto import decrypt_playerprefs_xml
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


if __name__ == "__main__":
    main()
