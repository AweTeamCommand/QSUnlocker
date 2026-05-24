import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import json
import os
import sys
import threading
import winreg
import ctypes
import shutil
from pathlib import Path

CONFIG_FILE = "struct.json"
VERSION = "1.0.0"
AUTHOR = "lemonademp"

DEFAULT_CONFIG = {
    "shell": {
        "default": "explorer.exe",
        "registry_path": "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon",
        "registry_key": "Shell"
    },
    "sethc": {
        "system32_path": "C:\\Windows\\System32",
        "sethc_file": "sethc.exe",
        "backup_suffix": ".bak",
        "replace_with": "cmd.exe"
    },
    "processes": {
        "critical_threshold": 50,
        "suspicious_threshold": 20,
        "update_interval": 2000,
        "critical_names": [
            "lsass.exe", "csrss.exe", "smss.exe", "wininit.exe",
            "services.exe", "winlogon.exe", "svchost.exe"
        ],
        "suspicious_names": [
            "powershell.exe", "cmd.exe", "mshta.exe", "wscript.exe",
            "cscript.exe", "regsvr32.exe", "rundll32.exe"
        ]
    },
    "restrictions": [
        {
            "name": "Debugger: Image File Execution Options",
            "description": "Перехват запуска процессов через IFEO Debugger",
            "registry_path": "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options",
            "action": "remove_debugger"
        },
        {
            "name": "DisableTaskMgr",
            "description": "Отключение Диспетчера задач через реестр",
            "registry_path": "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System",
            "registry_key": "DisableTaskMgr",
            "action": "delete_value"
        },
        {
            "name": "DisableRegistryTools",
            "description": "Блокировка редактора реестра",
            "registry_path": "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System",
            "registry_key": "DisableRegistryTools",
            "action": "delete_value"
        },
        {
            "name": "NoRun",
            "description": "Скрытие строки Выполнить из меню Пуск",
            "registry_path": "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer",
            "registry_key": "NoRun",
            "action": "delete_value"
        },
        {
            "name": "NoControlPanel",
            "description": "Блокировка открытия Панели управления",
            "registry_path": "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer",
            "registry_key": "NoControlPanel",
            "action": "delete_value"
        },
        {
            "name": "DisableCMD",
            "description": "Запрет запуска командной строки",
            "registry_path": "SOFTWARE\\Policies\\Microsoft\\Windows\\System",
            "registry_key": "DisableCMD",
            "action": "delete_value"
        }
    ],
    "autostart_registry": [
        "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
        "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce"
    ],
    "swap_mouse": {
        "description": "SwapMouseButton меняет кнопки мыши местами"
    },
    "theme": {
        "bg": "#1e1e1e",
        "fg": "#ffffff",
        "accent": "#3d8bcd",
        "btn_bg": "#2d2d2d",
        "btn_fg": "#ffffff",
        "entry_bg": "#2d2d2d",
        "entry_fg": "#ffffff",
        "highlight": "#3d8bcd",
        "danger": "#e05252",
        "warning": "#e0a040",
        "success": "#52a060",
        "header_bg": "#252526",
        "sidebar_bg": "#252526",
        "tab_active": "#3d8bcd",
        "tab_inactive": "#2d2d2d"
    },
    "window": {
        "title": "QSUnlocker",
        "width": 900,
        "height": 600,
        "min_width": 700,
        "min_height": 500
    }
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )


config = load_config()
theme = config.get("theme", DEFAULT_CONFIG["theme"])


class QSUnlocker(tk.Tk):
    def __init__(self):
        super().__init__()
        global config, theme
        config = load_config()
        theme = config.get("theme", DEFAULT_CONFIG["theme"])
        w = config["window"]
        self.title(w["title"])
        self.geometry(f"{w['width']}x{w['height']}")
        self.minsize(w["min_width"], w["min_height"])
        self.configure(bg=theme["bg"])
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        self._build_header()
        self._build_main()
        self._build_footer()

    def _build_header(self):
        header = tk.Frame(self, bg=theme["header_bg"], height=48)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(
            header, text="QSUnlocker", font=("Segoe UI", 16, "bold"),
            bg=theme["header_bg"], fg=theme["accent"]
        ).pack(side=tk.LEFT, padx=16, pady=8)
        admin_text = "  [Admin]" if is_admin() else "  [User]"
        admin_color = theme["success"] if is_admin() else theme["warning"]
        tk.Label(
            header, text=admin_text, font=("Segoe UI", 9),
            bg=theme["header_bg"], fg=admin_color
        ).pack(side=tk.LEFT, pady=8)

    def _build_main(self):
        main_frame = tk.Frame(self, bg=theme["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True)
        sidebar = tk.Frame(main_frame, bg=theme["sidebar_bg"], width=160)
        sidebar.pack(fill=tk.Y, side=tk.LEFT)
        sidebar.pack_propagate(False)
        self.content = tk.Frame(main_frame, bg=theme["bg"])
        self.content.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.pages = {}
        self.current_page = None
        categories = [
            ("Основное", "main_page"),
            ("Процессы", "proc_page"),
            ("Система", "sys_page"),
            ("Настройки", "settings_page"),
        ]
        self._sidebar_buttons = []
        for label, page_id in categories:
            btn = tk.Button(
                sidebar, text=label, font=("Segoe UI", 10),
                bg=theme["tab_inactive"], fg=theme["fg"],
                activebackground=theme["accent"], activeforeground="#fff",
                relief=tk.FLAT, bd=0, pady=12, cursor="hand2",
                command=lambda pid=page_id, lbl=label: self._switch_page(pid)
            )
            btn.pack(fill=tk.X, padx=0, pady=1)
            self._sidebar_buttons.append((btn, page_id))
        self._build_main_page()
        self._build_proc_page()
        self._build_sys_page()
        self._build_settings_page()
        self._switch_page("main_page")

    def _switch_page(self, page_id):
        for btn, pid in self._sidebar_buttons:
            if pid == page_id:
                btn.configure(bg=theme["accent"], fg="#fff")
            else:
                btn.configure(bg=theme["tab_inactive"], fg=theme["fg"])
        if self.current_page:
            self.current_page.pack_forget()
        page = self.pages.get(page_id)
        if page:
            page.pack(fill=tk.BOTH, expand=True)
            self.current_page = page

    def _section_label(self, parent, text):
        frame = tk.Frame(parent, bg=theme["bg"])
        frame.pack(fill=tk.X, padx=16, pady=(12, 2))
        tk.Label(
            frame, text=text.upper(), font=("Segoe UI", 8, "bold"),
            bg=theme["bg"], fg=theme["accent"]
        ).pack(anchor=tk.W)
        sep = tk.Frame(frame, bg=theme["accent"], height=1)
        sep.pack(fill=tk.X, pady=(2, 0))

    def _make_btn(self, parent, text, command, color=None, width=22):
        c = color if color else theme["btn_bg"]
        btn = tk.Button(
            parent, text=text, font=("Segoe UI", 9),
            bg=c, fg=theme["btn_fg"],
            activebackground=theme["accent"], activeforeground="#fff",
            relief=tk.FLAT, bd=0, pady=6, padx=10,
            cursor="hand2", width=width,
            command=command
        )
        return btn

    def _build_main_page(self):
        page = tk.Frame(self.content, bg=theme["bg"])
        self.pages["main_page"] = page
        canvas = tk.Canvas(page, bg=theme["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(page, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=theme["bg"])
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._section_label(scroll_frame, "Основное")
        btn_frame = tk.Frame(scroll_frame, bg=theme["bg"])
        btn_frame.pack(fill=tk.X, padx=16, pady=4)
        self._make_btn(btn_frame, "Перезапустить Explorer", self._restart_explorer).grid(row=0, column=0, padx=4, pady=4)
        self._make_btn(btn_frame, "Открыть Диспетчер задач", self._open_taskmgr).grid(row=0, column=1, padx=4, pady=4)
        self._make_btn(btn_frame, "Открыть CMD", self._open_cmd_window).grid(row=0, column=2, padx=4, pady=4)

        self._section_label(scroll_frame, "Мышь и доступность")
        btn_frame2 = tk.Frame(scroll_frame, bg=theme["bg"])
        btn_frame2.pack(fill=tk.X, padx=16, pady=4)
        self._make_btn(btn_frame2, "Отключить SwapMouseButton", self._disable_swap_mouse).grid(row=0, column=0, padx=4, pady=4)
        self._make_btn(btn_frame2, "Управление sethc.exe", self._open_sethc_window).grid(row=0, column=1, padx=4, pady=4)

        self._section_label(scroll_frame, "Безопасность")
        btn_frame3 = tk.Frame(scroll_frame, bg=theme["bg"])
        btn_frame3.pack(fill=tk.X, padx=16, pady=4)
        self._make_btn(btn_frame3, "Разблокировка ограничений", self._open_restrictions_window).grid(row=0, column=0, padx=4, pady=4)
        self._make_btn(btn_frame3, "Проверить Shell", self._open_shell_window).grid(row=0, column=1, padx=4, pady=4)

        self._section_label(scroll_frame, "Автозагрузка")
        btn_frame4 = tk.Frame(scroll_frame, bg=theme["bg"])
        btn_frame4.pack(fill=tk.X, padx=16, pady=4)
        self._make_btn(btn_frame4, "Автозагрузка приложений", self._open_autostart_window).grid(row=0, column=0, padx=4, pady=4)

    def _build_proc_page(self):
        page = tk.Frame(self.content, bg=theme["bg"])
        self.pages["proc_page"] = page
        self._section_label(page, "Мониторинг процессов")
        btn_frame = tk.Frame(page, bg=theme["bg"])
        btn_frame.pack(fill=tk.X, padx=16, pady=8)
        self._make_btn(btn_frame, "Следить за процессами", self._open_process_monitor, width=28).pack(anchor=tk.W)
        info = tk.Label(
            page,
            text="Открывает мини диспетчер задач с мониторингом CPU,\nуровнем критичности и управлением процессами.",
            font=("Segoe UI", 9), bg=theme["bg"], fg="#999999",
            justify=tk.LEFT
        )
        info.pack(anchor=tk.W, padx=20, pady=4)
        sep = tk.Frame(page, bg="#333", height=1)
        sep.pack(fill=tk.X, padx=16, pady=8)
        legend_frame = tk.Frame(page, bg=theme["bg"])
        legend_frame.pack(anchor=tk.W, padx=20)
        tk.Label(legend_frame, text="Легенда:", font=("Segoe UI", 9, "bold"),
                 bg=theme["bg"], fg=theme["fg"]).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        tk.Frame(legend_frame, bg=theme["danger"], width=16, height=16).grid(row=1, column=0, padx=(0, 8), pady=2)
        tk.Label(legend_frame, text="Критичный процесс — системный", font=("Segoe UI", 9),
                 bg=theme["bg"], fg=theme["fg"]).grid(row=1, column=1, sticky=tk.W)
        tk.Frame(legend_frame, bg=theme["warning"], width=16, height=16).grid(row=2, column=0, padx=(0, 8), pady=2)
        tk.Label(legend_frame, text="Подозрительный процесс", font=("Segoe UI", 9),
                 bg=theme["bg"], fg=theme["fg"]).grid(row=2, column=1, sticky=tk.W)
        tk.Frame(legend_frame, bg="#555555", width=16, height=16).grid(row=3, column=0, padx=(0, 8), pady=2)
        tk.Label(legend_frame, text="Обычный процесс", font=("Segoe UI", 9),
                 bg=theme["bg"], fg=theme["fg"]).grid(row=3, column=1, sticky=tk.W)

    def _build_sys_page(self):
        page = tk.Frame(self.content, bg=theme["bg"])
        self.pages["sys_page"] = page
        canvas = tk.Canvas(page, bg=theme["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(page, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=theme["bg"])
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._section_label(scroll_frame, "Управление системой")
        btn_frame = tk.Frame(scroll_frame, bg=theme["bg"])
        btn_frame.pack(fill=tk.X, padx=16, pady=4)
        self._make_btn(btn_frame, "Очистить временные файлы", self._clean_temp).grid(row=0, column=0, padx=4, pady=4)
        self._make_btn(btn_frame, "Перезапустить службу DNS", self._restart_dns).grid(row=0, column=1, padx=4, pady=4)
        self._make_btn(btn_frame, "Сбросить настройки сети", self._reset_network).grid(row=0, column=2, padx=4, pady=4)

        self._section_label(scroll_frame, "Обслуживание")
        btn_frame2 = tk.Frame(scroll_frame, bg=theme["bg"])
        btn_frame2.pack(fill=tk.X, padx=16, pady=4)
        self._make_btn(btn_frame2, "Проверить диск (chkdsk)", self._run_chkdsk).grid(row=0, column=0, padx=4, pady=4)
        self._make_btn(btn_frame2, "SFC /scannow", self._run_sfc).grid(row=0, column=1, padx=4, pady=4)
        self._make_btn(btn_frame2, "DISM RestoreHealth", self._run_dism).grid(row=0, column=2, padx=4, pady=4)

        self._section_label(scroll_frame, "Питание")
        btn_frame3 = tk.Frame(scroll_frame, bg=theme["bg"])
        btn_frame3.pack(fill=tk.X, padx=16, pady=4)
        self._make_btn(btn_frame3, "Перезагрузить систему", self._reboot_system, color=theme["warning"]).grid(row=0, column=0, padx=4, pady=4)
        self._make_btn(btn_frame3, "Завершить работу", self._shutdown_system, color=theme["danger"]).grid(row=0, column=1, padx=4, pady=4)
        self._make_btn(btn_frame3, "Гибернация", self._hibernate_system).grid(row=0, column=2, padx=4, pady=4)

        self._section_label(scroll_frame, "Брандмауэр и UAC")
        btn_frame4 = tk.Frame(scroll_frame, bg=theme["bg"])
        btn_frame4.pack(fill=tk.X, padx=16, pady=4)
        self._make_btn(btn_frame4, "Сброс правил брандмауэра", self._reset_firewall).grid(row=0, column=0, padx=4, pady=4)
        self._make_btn(btn_frame4, "Отключить UAC", self._disable_uac, color=theme["warning"]).grid(row=0, column=1, padx=4, pady=4)
        self._make_btn(btn_frame4, "Включить UAC", self._enable_uac).grid(row=0, column=2, padx=4, pady=4)

    def _build_settings_page(self):
        page = tk.Frame(self.content, bg=theme["bg"])
        self.pages["settings_page"] = page
        self._section_label(page, "Редактор struct.json")
        info = tk.Label(
            page,
            text="Здесь можно редактировать параметры конфигурации напрямую.",
            font=("Segoe UI", 9), bg=theme["bg"], fg="#999"
        )
        info.pack(anchor=tk.W, padx=20, pady=4)
        self.settings_text = scrolledtext.ScrolledText(
            page, font=("Consolas", 9),
            bg=theme["entry_bg"], fg=theme["entry_fg"],
            insertbackground=theme["fg"],
            relief=tk.FLAT, bd=0
        )
        self.settings_text.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            self.settings_text.insert("1.0", f.read())
        btn_frame = tk.Frame(page, bg=theme["bg"])
        btn_frame.pack(fill=tk.X, padx=16, pady=4)
        self._make_btn(btn_frame, "Сохранить изменения", self._save_settings, color=theme["success"]).pack(side=tk.LEFT, padx=4)
        self._make_btn(btn_frame, "Сбросить к стандартным", self._reset_settings, color=theme["warning"]).pack(side=tk.LEFT, padx=4)
        self._make_btn(btn_frame, "Обновить из файла", self._reload_settings).pack(side=tk.LEFT, padx=4)

    def _build_footer(self):
        footer = tk.Frame(self, bg=theme["header_bg"], height=28)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(
            footer,
            text=f"QSUnlocker v{VERSION}   |   Разработчик: {AUTHOR}",
            font=("Segoe UI", 8),
            bg=theme["header_bg"], fg="#888888"
        ).pack(side=tk.LEFT, padx=16, pady=4)

    def _restart_explorer(self):
        try:
            subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], check=False)
            subprocess.Popen(["explorer.exe"])
            messagebox.showinfo("QSUnlocker", "Explorer перезапущен.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _open_taskmgr(self):
        try:
            subprocess.Popen(["taskmgr.exe"])
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _open_cmd_window(self):
        win = tk.Toplevel(self)
        win.title("CMD — QSUnlocker")
        win.geometry("700x450")
        win.configure(bg=theme["bg"])
        tk.Label(win, text="Встроенная командная строка", font=("Segoe UI", 11, "bold"),
                 bg=theme["bg"], fg=theme["accent"]).pack(pady=8)
        output = scrolledtext.ScrolledText(
            win, font=("Consolas", 9),
            bg="#0c0c0c", fg="#cccccc",
            insertbackground="#fff",
            relief=tk.FLAT
        )
        output.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        input_frame = tk.Frame(win, bg=theme["bg"])
        input_frame.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(input_frame, text=">", font=("Consolas", 10),
                 bg=theme["bg"], fg=theme["accent"]).pack(side=tk.LEFT)
        cmd_var = tk.StringVar()
        cmd_entry = tk.Entry(
            input_frame, textvariable=cmd_var, font=("Consolas", 10),
            bg=theme["entry_bg"], fg=theme["entry_fg"],
            insertbackground=theme["fg"], relief=tk.FLAT
        )
        cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self._cmd_history = []
        self._cmd_hist_idx = [0]

        def run_cmd(event=None):
            cmd = cmd_var.get().strip()
            if not cmd:
                return
            self._cmd_history.append(cmd)
            self._cmd_hist_idx[0] = len(self._cmd_history)
            cmd_var.set("")
            output.insert(tk.END, f"\n> {cmd}\n")
            output.see(tk.END)

            def execute():
                try:
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True,
                        timeout=30, encoding="cp866", errors="replace"
                    )
                    out = result.stdout + result.stderr
                    output.insert(tk.END, out if out else "(нет вывода)\n")
                except subprocess.TimeoutExpired:
                    output.insert(tk.END, "Таймаут выполнения команды.\n")
                except Exception as e:
                    output.insert(tk.END, f"Ошибка: {e}\n")
                output.see(tk.END)

            threading.Thread(target=execute, daemon=True).start()

        def hist_up(event):
            if self._cmd_history and self._cmd_hist_idx[0] > 0:
                self._cmd_hist_idx[0] -= 1
                cmd_var.set(self._cmd_history[self._cmd_hist_idx[0]])

        def hist_down(event):
            if self._cmd_hist_idx[0] < len(self._cmd_history) - 1:
                self._cmd_hist_idx[0] += 1
                cmd_var.set(self._cmd_history[self._cmd_hist_idx[0]])
            else:
                self._cmd_hist_idx[0] = len(self._cmd_history)
                cmd_var.set("")

        cmd_entry.bind("<Return>", run_cmd)
        cmd_entry.bind("<Up>", hist_up)
        cmd_entry.bind("<Down>", hist_down)
        self._make_btn(input_frame, "Выполнить", run_cmd, width=10).pack(side=tk.LEFT, padx=4)
        output.insert(tk.END, "QSUnlocker CMD — введите команду и нажмите Enter\n")
        cmd_entry.focus()

    def _open_process_monitor(self):
        win = tk.Toplevel(self)
        win.title("Мониторинг процессов — QSUnlocker")
        win.geometry("750x500")
        win.configure(bg=theme["bg"])
        win.resizable(True, True)
        tk.Label(win, text="Мониторинг процессов", font=("Segoe UI", 11, "bold"),
                 bg=theme["bg"], fg=theme["accent"]).pack(pady=8)
        search_frame = tk.Frame(win, bg=theme["bg"])
        search_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(search_frame, text="Поиск:", font=("Segoe UI", 9),
                 bg=theme["bg"], fg=theme["fg"]).pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame, textvariable=search_var, font=("Segoe UI", 9),
            bg=theme["entry_bg"], fg=theme["entry_fg"],
            insertbackground=theme["fg"], relief=tk.FLAT, width=30
        )
        search_entry.pack(side=tk.LEFT, padx=6)
        columns = ("pid", "name", "cpu", "level")
        tree_frame = tk.Frame(win, bg=theme["bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=theme["btn_bg"],
                        foreground=theme["fg"],
                        fieldbackground=theme["btn_bg"],
                        rowheight=24,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background=theme["header_bg"],
                        foreground=theme["accent"],
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", theme["accent"])])
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        tree.heading("pid", text="PID")
        tree.heading("name", text="Имя процесса")
        tree.heading("cpu", text="CPU %")
        tree.heading("level", text="Уровень")
        tree.column("pid", width=60, anchor=tk.CENTER)
        tree.column("name", width=260)
        tree.column("cpu", width=80, anchor=tk.CENTER)
        tree.column("level", width=150, anchor=tk.CENTER)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.tag_configure("critical", foreground=theme["danger"])
        tree.tag_configure("suspicious", foreground=theme["warning"])
        tree.tag_configure("normal", foreground="#cccccc")
        btn_frame = tk.Frame(win, bg=theme["bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=6)
        status_var = tk.StringVar(value="Загрузка...")
        tk.Label(btn_frame, textvariable=status_var, font=("Segoe UI", 8),
                 bg=theme["bg"], fg="#888").pack(side=tk.LEFT)
        self._proc_running = True

        def get_level(name_lower):
            cr = [n.lower() for n in config["processes"]["critical_names"]]
            su = [n.lower() for n in config["processes"]["suspicious_names"]]
            if name_lower in cr:
                return "critical", "Критичный"
            if name_lower in su:
                return "suspicious", "Подозрительный"
            return "normal", "Обычный"

        def refresh_processes():
            if not self._proc_running:
                return
            search = search_var.get().strip().lower()
            try:
                result = subprocess.run(
                    ["tasklist", "/fo", "csv", "/nh"],
                    capture_output=True, text=True,
                    encoding="cp866", errors="replace"
                )
                lines = result.stdout.strip().splitlines()
                procs = []
                for line in lines:
                    parts = line.replace('"', '').split(',')
                    if len(parts) >= 2:
                        pname = parts[0].strip()
                        pid = parts[1].strip()
                        procs.append((pid, pname))
                if search:
                    procs = [(pid, pn) for pid, pn in procs if search in pn.lower()]
                cpu_result = subprocess.run(
                    ["wmic", "process", "get", "ProcessId,PercentProcessorTime", "/format:csv"],
                    capture_output=True, text=True, encoding="cp866", errors="replace"
                )
                cpu_map = {}
                for line in cpu_result.stdout.splitlines():
                    parts = line.strip().split(",")
                    if len(parts) >= 3:
                        try:
                            cpu_map[parts[2].strip()] = parts[1].strip()
                        except:
                            pass
                selected = tree.focus()
                sel_pid = None
                if selected:
                    vals = tree.item(selected, "values")
                    if vals:
                        sel_pid = vals[0]
                for item in tree.get_children():
                    tree.delete(item)
                restore_sel = None
                for pid, pname in procs:
                    cpu_val = cpu_map.get(pid, "0")
                    try:
                        cpu_f = float(cpu_val)
                    except:
                        cpu_f = 0.0
                    tag, level_text = get_level(pname.lower())
                    iid = tree.insert("", tk.END, values=(pid, pname, f"{cpu_f:.1f}%", level_text), tags=(tag,))
                    if pid == sel_pid:
                        restore_sel = iid
                if restore_sel:
                    tree.focus(restore_sel)
                    tree.selection_set(restore_sel)
                status_var.set(f"Процессов: {len(procs)}  |  Обновлено")
            except Exception as e:
                status_var.set(f"Ошибка: {e}")
            if self._proc_running:
                interval = config["processes"].get("update_interval", 2000)
                win.after(interval, refresh_processes)

        def kill_selected():
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("QSUnlocker", "Выберите процесс.")
                return
            vals = tree.item(sel, "values")
            if not vals:
                return
            pid, pname = vals[0], vals[1]
            if not messagebox.askyesno("Завершить", f"Завершить процесс {pname} (PID: {pid})?"):
                return
            try:
                subprocess.run(["taskkill", "/F", "/PID", pid], check=True)
                status_var.set(f"Процесс {pname} завершён.")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        self._make_btn(btn_frame, "Завершить процесс", kill_selected, color=theme["danger"]).pack(side=tk.RIGHT, padx=4)
        self._make_btn(btn_frame, "Обновить сейчас", refresh_processes).pack(side=tk.RIGHT, padx=4)

        def on_close():
            self._proc_running = False
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)
        refresh_processes()

    def _open_autostart_window(self):
        win = tk.Toplevel(self)
        win.title("Автозагрузка — QSUnlocker")
        win.geometry("700x450")
        win.configure(bg=theme["bg"])
        tk.Label(win, text="Автозагрузка приложений", font=("Segoe UI", 11, "bold"),
                 bg=theme["bg"], fg=theme["accent"]).pack(pady=8)
        columns = ("source", "name", "command")
        tree_frame = tk.Frame(win, bg=theme["bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        style = ttk.Style()
        style.configure("Treeview",
                        background=theme["btn_bg"],
                        foreground=theme["fg"],
                        fieldbackground=theme["btn_bg"],
                        rowheight=24,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background=theme["header_bg"],
                        foreground=theme["accent"],
                        font=("Segoe UI", 9, "bold"))
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        tree.heading("source", text="Раздел")
        tree.heading("name", text="Имя")
        tree.heading("command", text="Команда")
        tree.column("source", width=160)
        tree.column("name", width=160)
        tree.column("command", width=280)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        entries_map = {}

        def load_autostart():
            for item in tree.get_children():
                tree.delete(item)
            entries_map.clear()
            reg_paths = config.get("autostart_registry", DEFAULT_CONFIG["autostart_registry"])
            for reg_path in reg_paths:
                for hive, hive_name in [(winreg.HKEY_CURRENT_USER, "HKCU"), (winreg.HKEY_LOCAL_MACHINE, "HKLM")]:
                    try:
                        key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_READ)
                        i = 0
                        while True:
                            try:
                                name, val, _ = winreg.EnumValue(key, i)
                                source = f"{hive_name}\\...\\{reg_path.split(chr(92))[-1]}"
                                iid = tree.insert("", tk.END, values=(source, name, val))
                                entries_map[iid] = (hive, reg_path, name)
                                i += 1
                            except OSError:
                                break
                        winreg.CloseKey(key)
                    except Exception:
                        pass

        def disable_selected():
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("QSUnlocker", "Выберите запись.")
                return
            info = entries_map.get(sel)
            if not info:
                return
            hive, reg_path, name = info
            if not messagebox.askyesno("Отключить", f"Отключить автозапуск для '{name}'?"):
                return
            try:
                key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, name)
                winreg.CloseKey(key)
                load_autostart()
                messagebox.showinfo("QSUnlocker", f"'{name}' удалён из автозагрузки.")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        btn_frame = tk.Frame(win, bg=theme["bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=6)
        self._make_btn(btn_frame, "Отключить автозапуск", disable_selected, color=theme["warning"]).pack(side=tk.LEFT, padx=4)
        self._make_btn(btn_frame, "Обновить", load_autostart).pack(side=tk.LEFT, padx=4)
        load_autostart()

    def _open_restrictions_window(self):
        win = tk.Toplevel(self)
        win.title("Разблокировка ограничений — QSUnlocker")
        win.geometry("680x480")
        win.configure(bg=theme["bg"])
        tk.Label(win, text="Ограничения системы", font=("Segoe UI", 11, "bold"),
                 bg=theme["bg"], fg=theme["accent"]).pack(pady=8)
        columns = ("name", "description", "status")
        tree_frame = tk.Frame(win, bg=theme["bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        style = ttk.Style()
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        tree.heading("name", text="Ограничение")
        tree.heading("description", text="Описание")
        tree.heading("status", text="Статус")
        tree.column("name", width=180)
        tree.column("description", width=300)
        tree.column("status", width=100, anchor=tk.CENTER)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.tag_configure("active", foreground=theme["danger"])
        tree.tag_configure("inactive", foreground=theme["success"])

        def check_restriction(r):
            action = r.get("action", "")
            if action == "delete_value":
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r["registry_path"], 0, winreg.KEY_READ)
                    winreg.QueryValueEx(key, r["registry_key"])
                    winreg.CloseKey(key)
                    return True
                except:
                    return False
            elif action == "remove_debugger":
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r["registry_path"], 0, winreg.KEY_READ)
                    i = 0
                    found = False
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)
                            try:
                                winreg.QueryValueEx(subkey, "Debugger")
                                found = True
                                winreg.CloseKey(subkey)
                                break
                            except:
                                pass
                            winreg.CloseKey(subkey)
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                    return found
                except:
                    return False
            return False

        def load_restrictions():
            for item in tree.get_children():
                tree.delete(item)
            for r in config.get("restrictions", []):
                active = check_restriction(r)
                status = "Активно" if active else "Не найдено"
                tag = "active" if active else "inactive"
                tree.insert("", tk.END, values=(r["name"], r["description"], status), tags=(tag,))

        def remove_restriction(r):
            action = r.get("action", "")
            if action == "delete_value":
                for hive in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
                    try:
                        key = winreg.OpenKey(hive, r["registry_path"], 0, winreg.KEY_SET_VALUE)
                        winreg.DeleteValue(key, r["registry_key"])
                        winreg.CloseKey(key)
                    except:
                        pass
            elif action == "remove_debugger":
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE, r["registry_path"],
                        0, winreg.KEY_READ | winreg.KEY_WRITE
                    )
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
                            try:
                                winreg.QueryValueEx(subkey, "Debugger")
                                winreg.DeleteValue(subkey, "Debugger")
                            except:
                                pass
                            winreg.CloseKey(subkey)
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except:
                    pass

        def remove_all():
            if not messagebox.askyesno("Снять все", "Снять все найденные ограничения?"):
                return
            for r in config.get("restrictions", []):
                remove_restriction(r)
            load_restrictions()
            messagebox.showinfo("QSUnlocker", "Все ограничения обработаны.")

        def remove_selected():
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("QSUnlocker", "Выберите ограничение.")
                return
            idx = tree.index(sel)
            restrictions = config.get("restrictions", [])
            if idx < len(restrictions):
                remove_restriction(restrictions[idx])
                load_restrictions()

        btn_frame = tk.Frame(win, bg=theme["bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=6)
        self._make_btn(btn_frame, "Снять все", remove_all, color=theme["danger"]).pack(side=tk.LEFT, padx=4)
        self._make_btn(btn_frame, "Снять выбранное", remove_selected, color=theme["warning"]).pack(side=tk.LEFT, padx=4)
        self._make_btn(btn_frame, "Обновить", load_restrictions).pack(side=tk.LEFT, padx=4)
        load_restrictions()

    def _open_shell_window(self):
        win = tk.Toplevel(self)
        win.title("Проверить Shell — QSUnlocker")
        win.geometry("520x240")
        win.configure(bg=theme["bg"])
        tk.Label(win, text="Текущий Shell процесс", font=("Segoe UI", 11, "bold"),
                 bg=theme["bg"], fg=theme["accent"]).pack(pady=12)

        def get_current_shell():
            try:
                shell_cfg = config.get("shell", DEFAULT_CONFIG["shell"])
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    shell_cfg["registry_path"], 0, winreg.KEY_READ
                )
                val, _ = winreg.QueryValueEx(key, shell_cfg["registry_key"])
                winreg.CloseKey(key)
                return val
            except Exception as e:
                return f"Ошибка: {e}"

        shell_val = tk.StringVar(value=get_current_shell())
        info_frame = tk.Frame(win, bg=theme["btn_bg"])
        info_frame.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(info_frame, text="Shell:", font=("Segoe UI", 9, "bold"),
                 bg=theme["btn_bg"], fg=theme["fg"]).grid(row=0, column=0, padx=10, pady=8, sticky=tk.W)
        shell_label = tk.Label(info_frame, textvariable=shell_val, font=("Consolas", 10),
                               bg=theme["btn_bg"], fg=theme["success"])
        shell_label.grid(row=0, column=1, padx=10, pady=8, sticky=tk.W)
        default_val = config.get("shell", DEFAULT_CONFIG["shell"]).get("default", "explorer.exe")
        tk.Label(win, text=f"Стандартное значение: {default_val}",
                 font=("Segoe UI", 8), bg=theme["bg"], fg="#888").pack(pady=2)

        def reset_shell():
            try:
                shell_cfg = config.get("shell", DEFAULT_CONFIG["shell"])
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    shell_cfg["registry_path"], 0, winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, shell_cfg["registry_key"], 0, winreg.REG_SZ, shell_cfg["default"])
                winreg.CloseKey(key)
                shell_val.set(get_current_shell())
                messagebox.showinfo("QSUnlocker", "Shell сброшен к стандартному значению.")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        def refresh_shell():
            shell_val.set(get_current_shell())

        btn_frame = tk.Frame(win, bg=theme["bg"])
        btn_frame.pack(pady=10)
        self._make_btn(btn_frame, "Сбросить", reset_shell, color=theme["warning"]).pack(side=tk.LEFT, padx=6)
        self._make_btn(btn_frame, "Обновить", refresh_shell).pack(side=tk.LEFT, padx=6)

    def _disable_swap_mouse(self):
        try:
            result = ctypes.windll.user32.SwapMouseButton(False)
            if result:
                messagebox.showinfo("QSUnlocker", "SwapMouseButton отключён. Кнопки мыши восстановлены.")
            else:
                messagebox.showinfo("QSUnlocker", "SwapMouseButton уже был отключён.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _open_sethc_window(self):
        win = tk.Toplevel(self)
        win.title("Управление sethc.exe — QSUnlocker")
        win.geometry("560x320")
        win.configure(bg=theme["bg"])
        tk.Label(win, text="Управление sethc.exe (Залипание клавиш)", font=("Segoe UI", 11, "bold"),
                 bg=theme["bg"], fg=theme["accent"]).pack(pady=10)
        sethc_cfg = config.get("sethc", DEFAULT_CONFIG["sethc"])
        sys32 = sethc_cfg["system32_path"]
        sethc_file = sethc_cfg["sethc_file"]
        backup_suffix = sethc_cfg["backup_suffix"]
        replace_with = sethc_cfg["replace_with"]
        sethc_path = os.path.join(sys32, sethc_file)
        backup_path = sethc_path + backup_suffix
        replace_path = os.path.join(sys32, replace_with)

        def get_status():
            if os.path.exists(backup_path):
                return "sethc.exe заменён (backup существует)", theme["warning"]
            elif os.path.exists(sethc_path):
                return "sethc.exe оригинальный", theme["success"]
            return "sethc.exe не найден", theme["danger"]

        status_text, status_color = get_status()
        status_var = tk.StringVar(value=status_text)
        status_color_var = [status_color]
        status_lbl = tk.Label(win, textvariable=status_var, font=("Segoe UI", 9),
                              bg=theme["bg"], fg=status_color_var[0])
        status_lbl.pack(pady=4)
        info_frame = tk.Frame(win, bg=theme["btn_bg"])
        info_frame.pack(fill=tk.X, padx=20, pady=8)
        for row, (k, v) in enumerate([
            ("sethc.exe", sethc_path),
            ("Backup", backup_path),
            ("Заменяется на", replace_path)
        ]):
            tk.Label(info_frame, text=f"{k}:", font=("Segoe UI", 9, "bold"),
                     bg=theme["btn_bg"], fg=theme["fg"]).grid(row=row, column=0, padx=10, pady=4, sticky=tk.W)
            tk.Label(info_frame, text=v, font=("Consolas", 8),
                     bg=theme["btn_bg"], fg="#aaaaaa").grid(row=row, column=1, padx=10, pady=4, sticky=tk.W)

        def refresh_status():
            st, sc = get_status()
            status_var.set(st)
            status_color_var[0] = sc
            status_lbl.configure(fg=sc)

        def replace_sethc():
            if not is_admin():
                messagebox.showerror("Права", "Требуются права администратора.")
                return
            if os.path.exists(backup_path):
                messagebox.showwarning("QSUnlocker", "Backup уже существует. Сначала восстановите оригинал.")
                return
            if not messagebox.askyesno("Подтверждение", f"Заменить {sethc_file} на {replace_with}?\nБудет создан backup."):
                return
            try:
                subprocess.run(["takeown", "/f", sethc_path], check=True, capture_output=True)
                subprocess.run(["icacls", sethc_path, "/grant", "Administrators:F"], check=True, capture_output=True)
                shutil.copy2(sethc_path, backup_path)
                shutil.copy2(replace_path, sethc_path)
                refresh_status()
                messagebox.showinfo("QSUnlocker", f"sethc.exe заменён на {replace_with}.")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        def restore_sethc():
            if not is_admin():
                messagebox.showerror("Права", "Требуются права администратора.")
                return
            if not os.path.exists(backup_path):
                messagebox.showwarning("QSUnlocker", "Backup не найден.")
                return
            if not messagebox.askyesno("Подтверждение", "Восстановить оригинальный sethc.exe?"):
                return
            try:
                shutil.copy2(backup_path, sethc_path)
                os.remove(backup_path)
                refresh_status()
                messagebox.showinfo("QSUnlocker", "sethc.exe восстановлен.")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        btn_frame = tk.Frame(win, bg=theme["bg"])
        btn_frame.pack(pady=10)
        self._make_btn(btn_frame, "Заменить sethc.exe", replace_sethc, color=theme["warning"]).pack(side=tk.LEFT, padx=6)
        self._make_btn(btn_frame, "Восстановить оригинал", restore_sethc, color=theme["success"]).pack(side=tk.LEFT, padx=6)
        self._make_btn(btn_frame, "Обновить статус", refresh_status).pack(side=tk.LEFT, padx=6)

    def _save_settings(self):
        try:
            text = self.settings_text.get("1.0", tk.END)
            parsed = json.loads(text)
            save_config(parsed)
            global config, theme
            config = parsed
            theme = config.get("theme", DEFAULT_CONFIG["theme"])
            messagebox.showinfo("QSUnlocker", "Настройки сохранены. Перезапустите программу для применения темы.")
        except json.JSONDecodeError as e:
            messagebox.showerror("Ошибка JSON", f"Неверный формат JSON:\n{e}")

    def _reset_settings(self):
        if not messagebox.askyesno("Сброс", "Сбросить все настройки к стандартным?"):
            return
        save_config(DEFAULT_CONFIG)
        self.settings_text.delete("1.0", tk.END)
        self.settings_text.insert("1.0", json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=4))
        messagebox.showinfo("QSUnlocker", "Настройки сброшены.")

    def _reload_settings(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            self.settings_text.delete("1.0", tk.END)
            self.settings_text.insert("1.0", content)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _clean_temp(self):
        if not messagebox.askyesno("Очистка", "Очистить временные файлы (Temp)?"):
            return
        temp_dirs = [os.environ.get("TEMP", ""), os.environ.get("TMP", ""),
                     os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Temp")]
        removed = 0
        errors = 0
        for temp_dir in temp_dirs:
            if not temp_dir or not os.path.exists(temp_dir):
                continue
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    removed += 1
                except:
                    errors += 1
        messagebox.showinfo("Очистка", f"Удалено: {removed} объектов\nОшибок: {errors}")

    def _restart_dns(self):
        try:
            subprocess.run(["net", "stop", "dnscache"], check=False, capture_output=True)
            subprocess.run(["net", "start", "dnscache"], check=False, capture_output=True)
            messagebox.showinfo("QSUnlocker", "Служба DNS Client перезапущена.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _reset_network(self):
        if not messagebox.askyesno("Сброс сети", "Сбросить настройки сети? Потребуется перезагрузка."):
            return
        try:
            cmds = [
                ["netsh", "winsock", "reset"],
                ["netsh", "int", "ip", "reset"],
                ["ipconfig", "/release"],
                ["ipconfig", "/flushdns"],
                ["ipconfig", "/renew"],
            ]
            for cmd in cmds:
                subprocess.run(cmd, capture_output=True)
            messagebox.showinfo("QSUnlocker", "Настройки сети сброшены. Рекомендуется перезагрузка.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _run_chkdsk(self):
        try:
            subprocess.Popen(
                ["cmd", "/k", "chkdsk C: /f /r"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _run_sfc(self):
        if not is_admin():
            messagebox.showerror("Права", "Требуются права администратора.")
            return
        try:
            subprocess.Popen(
                ["cmd", "/k", "sfc /scannow"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _run_dism(self):
        if not is_admin():
            messagebox.showerror("Права", "Требуются права администратора.")
            return
        try:
            subprocess.Popen(
                ["cmd", "/k", "DISM /Online /Cleanup-Image /RestoreHealth"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _reboot_system(self):
        if not messagebox.askyesno("Перезагрузка", "Перезагрузить систему сейчас?"):
            return
        try:
            subprocess.run(["shutdown", "/r", "/t", "0"])
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _shutdown_system(self):
        if not messagebox.askyesno("Выключение", "Завершить работу системы сейчас?"):
            return
        try:
            subprocess.run(["shutdown", "/s", "/t", "0"])
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _hibernate_system(self):
        if not messagebox.askyesno("Гибернация", "Перевести систему в режим гибернации?"):
            return
        try:
            subprocess.run(["shutdown", "/h"])
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _reset_firewall(self):
        if not messagebox.askyesno("Брандмауэр", "Сбросить все правила брандмауэра Windows?"):
            return
        try:
            subprocess.run(["netsh", "advfirewall", "reset"], check=True, capture_output=True)
            messagebox.showinfo("QSUnlocker", "Правила брандмауэра сброшены.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _disable_uac(self):
        if not is_admin():
            messagebox.showerror("Права", "Требуются права администратора.")
            return
        if not messagebox.askyesno("UAC", "Отключить контроль учётных записей (UAC)?"):
            return
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            messagebox.showinfo("QSUnlocker", "UAC отключён. Требуется перезагрузка.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _enable_uac(self):
        if not is_admin():
            messagebox.showerror("Права", "Требуются права администратора.")
            return
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            messagebox.showinfo("QSUnlocker", "UAC включён. Требуется перезагрузка.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


if __name__ == "__main__":
    app = QSUnlocker()
    app.mainloop()