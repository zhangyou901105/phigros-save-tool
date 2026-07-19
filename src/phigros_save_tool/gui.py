"""Phigros Save Manager GUI - 基于 tkinter 的存档编辑器。"""

import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from phigros_save_tool.crypto import decrypt_playerprefs_xml, encrypt_to_playerprefs_xml


class PhigrosSaveEditor:
    """Phigros 存档编辑器 GUI。"""

    def __init__(self, root):
        self.root = root
        self.root.title("Phigros Save Manager v2.0")
        self.root.geometry("1200x800")

        self.entries = {}
        self.current_file = None

        self._build_ui()

    def _build_ui(self):
        # 顶部工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="打开", command=self.load_save).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="保存", command=self.save_save).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="新建", command=self.new_save).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="导出JSON", command=self.export_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导入JSON", command=self.import_json).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="全满分", command=self.fill_all_scores).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="消除红点", command=self.fix_collection_red_dots).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="补全章节", command=self.fill_chapter_progress).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="补全AT/INS", command=self.fill_special_unlocks).pack(side=tk.LEFT, padx=2)

        # 搜索栏
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.LEFT, padx=(20, 5))
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search)
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)

        # 分类选择
        cat_frame = ttk.Frame(toolbar)
        cat_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(cat_frame, text="分类:").pack(side=tk.LEFT)
        self.cat_var = tk.StringVar(value="全部")
        self.cat_combo = ttk.Combobox(cat_frame, textvariable=self.cat_var, state="readonly", width=15)
        self.cat_combo["values"] = [c[0] for c in self.CATEGORIES]
        self.cat_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_entries())
        self.cat_combo.pack(side=tk.LEFT, padx=5)

        # 统计信息
        self.stat_var = tk.StringVar(value="未加载存档")
        ttk.Label(toolbar, textvariable=self.stat_var, foreground="blue").pack(side=tk.RIGHT, padx=5)

        # 主区域：左右分栏
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧：快捷操作
        left_frame = ttk.Frame(main_paned, width=220)
        main_paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="快捷操作", font=("Arial", 12, "bold")).pack(pady=5)

        btn_config = {"width": 18, "height": 2}
        ttk.Button(left_frame, text="设置\nGameCompleted=3.0", **btn_config,
                   command=lambda: self.set_key("GameCompleted", "3.0")).pack(pady=2)
        ttk.Button(left_frame, text="设置\nchallengeModeRank=551", **btn_config,
                   command=lambda: self.set_key("challengeModeRank", "551")).pack(pady=2)
        ttk.Button(left_frame, text="设置\n课题模式=蓝色30", **btn_config,
                   command=lambda: self.set_key("challengeModeRank", "230")).pack(pady=2)
        ttk.Button(left_frame, text="设置\n课题模式=金色99", **btn_config,
                   command=lambda: self.set_key("challengeModeRank", "499")).pack(pady=2)
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Button(left_frame, text="消除所有\n红点", **btn_config,
                   command=self.fix_collection_red_dots).pack(pady=2)
        ttk.Button(left_frame, text="补全\n章节进度", **btn_config,
                   command=self.fill_chapter_progress).pack(pady=2)
        ttk.Button(left_frame, text="补全\nAT/INSGrade", **btn_config,
                   command=self.fill_special_unlocks).pack(pady=2)

        # 右侧：条目列表
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=4)

        columns = ("name", "value")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("name", text="键名")
        self.tree.heading("value", text="值")
        self.tree.column("name", width=400)
        self.tree.column("value", width=700)

        scrollbar_y = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 底部状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=5, pady=2)
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var, foreground="gray").pack(side=tk.LEFT)

        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="编辑选中项", command=self.edit_selected)
        self.menu.add_command(label="删除选中项", command=self.delete_selected)
        self.tree.bind("<Button-3>", self.show_context_menu)

    # ============================================================
    # 分类定义
    # ============================================================

    CATEGORIES = [
        ("全部", lambda k: True),
        ("成绩记录", lambda k: ".Record." in k),
        ("歌曲解锁", lambda k: k.startswith("0key")),
        ("收藏解锁", lambda k: k.startswith("1key")),
        ("插画解锁", lambda k: k.startswith("2key")),
        ("头像解锁", lambda k: k.startswith("3key")),
        ("章节进度", lambda k: any(x in k for x in ["chapter", "C8", "randomVersion", "finishLegacy", "legacyChapter"])),
        ("特殊解锁", lambda k: any(x in k for x in ["unlockFlagOf", "INSGrade", "challengeModeRank", "GameCompleted"])),
        ("玩家设置", lambda k: k.startswith(("player", "musicVolume", "SEVolume", "offset", "chordSupport", "autoSync", "Guid", "playerID"))),
        ("其他", lambda k: True),
    ]

    def _matches_category(self, key, cat_name):
        if cat_name == "全部":
            return True
        for name, func in self.CATEGORIES:
            if name == cat_name:
                return func(key)
        return True

    # ============================================================
    # 文件操作
    # ============================================================

    def load_save(self):
        path = filedialog.askopenfilename(
            title="选择存档文件",
            filetypes=[("PlayerPrefs XML", "*.xml"), ("所有文件", "*.*")]
        )
        if not path:
            return
        try:
            entries, failed = decrypt_playerprefs_xml(path)
            self.entries = entries
            self.current_file = path
            self.refresh_entries()
            self.update_stats()
            self.status_var.set(f"已加载：{path}")
            messagebox.showinfo("成功", f"已加载 {len(entries)} 个条目\n解密失败：{len(failed)} 个")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败：{e}")

    def save_save(self):
        if not self.entries:
            messagebox.showwarning("警告", "没有可保存的内容")
            return
        path = filedialog.asksaveasfilename(
            title="保存存档",
            defaultextension=".xml",
            filetypes=[("PlayerPrefs XML", "*.xml"), ("所有文件", "*.*")]
        )
        if not path:
            return
        try:
            size = encrypt_to_playerprefs_xml(self.entries, path)
            self.current_file = path
            self.status_var.set(f"已保存：{path} ({size:,} bytes)")
            messagebox.showinfo("成功", f"已保存 {len(self.entries)} 个条目\n大小：{size:,} bytes")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}")

    def new_save(self):
        if self.entries and not messagebox.askyesno("确认", "确定要新建空白存档吗？当前修改将丢失。"):
            return
        self.entries = {}
        self.current_file = None
        self.refresh_entries()
        self.update_stats()
        self.status_var.set("新建空白存档")

    def export_json(self):
        if not self.entries:
            messagebox.showwarning("警告", "没有内容可导出")
            return
        path = filedialog.asksaveasfilename(
            title="导出 JSON", defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)
        self.status_var.set(f"已导出：{path}")

    def import_json(self):
        path = filedialog.askopenfilename(title="导入 JSON", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.entries = data
                self.refresh_entries()
                self.update_stats()
                self.status_var.set(f"已导入：{path}")
            else:
                messagebox.showerror("错误", "JSON 格式错误，应为字典")
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{e}")

    # ============================================================
    # 视图刷新
    # ============================================================

    def on_search(self, *args):
        self.refresh_entries()

    def refresh_entries(self, search=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = (search or self.search_var.get()).lower()
        cat_name = self.cat_var.get()

        filtered = []
        for key, value in self.entries.items():
            if not self._matches_category(key, cat_name):
                continue
            if search and search not in key.lower() and search not in value.lower():
                continue
            filtered.append((key, value))

        filtered.sort(key=lambda x: x[0].lower())

        for key, value in filtered:
            display_value = value[:300] + "..." if len(value) > 300 else value
            self.tree.insert("", tk.END, values=(key, display_value))

        self.stat_var.set(f"显示：{len(filtered)} / {len(self.entries)} | 分类：{cat_name}")

    def update_stats(self):
        records = sum(1 for k in self.entries if ".Record." in k)
        songs = sum(1 for k in self.entries if k.startswith("0key"))
        collections = sum(1 for k in self.entries if k.startswith("1key"))
        illustrations = sum(1 for k in self.entries if k.startswith("2key"))
        portraits = sum(1 for k in self.entries if k.startswith("3key"))
        self.stat_var.set(
            f"总：{len(self.entries)} | 成绩：{records} | "
            f"歌曲：{songs} | 收藏：{collections} | "
            f"插画：{illustrations} | 头像：{portraits}"
        )

    # ============================================================
    # 快捷操作
    # ============================================================

    def set_key(self, key, value):
        self.entries[key] = value
        self.refresh_entries()
        self.status_var.set(f"已设置 {key} = {value}")

    def fill_all_scores(self):
        count = 0
        full_score = '{"s":1000000,"a":100.0,"c":2}'
        for key in list(self.entries.keys()):
            if ".Record." in key:
                self.entries[key] = full_score
                count += 1
        self.refresh_entries()
        self.update_stats()
        self.status_var.set(f"已设置 {count} 条成绩为 AP")
        messagebox.showinfo("完成", f"已将 {count} 条成绩设为 AP (1000000)")

    def fix_collection_red_dots(self):
        count = 0
        for key in list(self.entries.keys()):
            if key.endswith("CollectionTextOpened"):
                self.entries[key] = "2"
                count += 1
        self.refresh_entries()
        self.status_var.set(f"已修复 {count} 个 CollectionTextOpened")
        messagebox.showinfo("完成", f"已修复 {count} 个红点标记")

    def fill_chapter_progress(self):
        flags = [
            "GameCompleted", "finishLegacyChapter", "completed",
            "chapter8Passed", "chapter8UnlockBegin", "chapter8UnlockSecondPhase",
        ]
        values = ["3.0", "True", "312", "True", "True", "True"]
        for key, val in zip(flags, values):
            self.entries[key] = val

        for i in range(6):
            self.entries[f"chapter8SongUnlocked[{i}]"] = "True"
            self.entries[f"randomVersionUnlocked[{i}]"] = "True"

        c8_keys = [
            "C8CraveWaveUnlocked", "C8DESTRUCTION321Unlocked", "C8DistortedFateUnlocked",
            "C8LuminescenceUnlocked", "C8RetributionUnlocked", "C8TheChariotREVIIVALUnlocked",
        ]
        for ck in c8_keys:
            self.entries[ck] = "True"

        self.refresh_entries()
        self.status_var.set("已补全章节进度")
        messagebox.showinfo("完成", "已补全章节进度和 C8 解锁标志")

    def fill_special_unlocks(self):
        at_songs = ["Igallta", "Rrharil", "Spasmodic"]
        for song in at_songs:
            for diff in ["EZ", "HD", "IN", "AT"]:
                self.entries[f"unlockFlagOf{song}{diff}"] = "True"

        ins_songs = [
            "Cuvism", "DESTRUCTION321", "DistortedFate", "Shadow", "Stasis",
            "YouaretheMiserable", "atruthseekerCommunicationwithUtopiawillbelost",
            "iLArtifact", "inferior", "心之所向",
        ]
        for song in ins_songs:
            self.entries[f"{song}INSGrade"] = "True"

        self.refresh_entries()
        self.status_var.set("已补全特殊解锁")
        messagebox.showinfo("完成", "已补全 AT 解锁标志和 INSGrade")

    # ============================================================
    # 编辑操作
    # ============================================================

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选中一个条目")
            return

        item = self.tree.item(selected[0])
        current_value = item["values"][1]

        dialog = tk.Toplevel(self.root)
        dialog.title("编辑条目")
        dialog.geometry("700x350")
        dialog.transient(self.root)

        ttk.Label(dialog, text=f"键名：{item['values'][0]}", font=("Arial", 10, "bold")).pack(pady=5, anchor="w")
        text = tk.Text(dialog, height=12, width=80)
        text.pack(pady=5, padx=10)
        text.insert("1.0", current_value)

        def save_edit():
            new_value = text.get("1.0", "end-1c")
            key = item["values"][0]
            self.entries[key] = new_value
            self.refresh_entries()
            self.update_stats()
            dialog.destroy()

        ttk.Button(dialog, text="保存", command=save_edit).pack(pady=5)
        ttk.Button(dialog, text="取消", command=dialog.destroy).pack(pady=2)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        keys = [self.tree.item(s)["values"][0] for s in selected]
        for key in keys:
            del self.entries[key]
        self.refresh_entries()
        self.update_stats()
        self.status_var.set(f"已删除 {len(keys)} 个条目")

    def show_context_menu(self, event):
        self.tree.selection_set(event.y)
        self.menu.post(event.x_root, event.y_root)


def main():
    root = tk.Tk()
    app = PhigrosSaveEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
