#!/usr/bin/env python3
import shlex
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

APP_TITLE = "Zapret Control"
SERVICE_NAME = "zapret"

# Цветовая схема (Dark Theme)
COLORS = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "accent": "#0078d4",
    "secondary_bg": "#2d2d2d",
    "border": "#3f3f3f",
    "success": "#28a745",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#17a2b8"
}

class ZapretControlApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("900x700")
        self.root.minsize(850, 650)
        self.root.configure(bg=COLORS["bg"])

        self.status_var = tk.StringVar(value="Состояние: неизвестно")
        self.terminal_var = tk.StringVar(value="Терминал: поиск...")
        
        self._setup_styles()
        self._build_ui()
        
        self.detected_terminal = self._detect_terminal()
        self.terminal_var.set(
            f"Терминал: {self.detected_terminal[0]}" if self.detected_terminal else "Терминал: не найден"
        )
        self.refresh_status()
        self.load_status_details()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Общие стили для фреймов
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["fg"])
        
        # Стили для кнопок
        style.configure("Accent.TButton", 
                        background=COLORS["accent"], 
                        foreground="white", 
                        font=("Segoe UI", 10, "bold"),
                        padding=10)
        style.map("Accent.TButton", background=[("active", "#005a9e")])

        style.configure("TButton", 
                        background=COLORS["secondary_bg"], 
                        foreground=COLORS["fg"], 
                        padding=10)
        style.map("TButton", background=[("active", COLORS["border"])])

        # Стили для LabelFrame
        style.configure("TLabelframe", background=COLORS["bg"], foreground=COLORS["fg"], bordercolor=COLORS["border"])
        style.configure("TLabelframe.Label", background=COLORS["bg"], foreground=COLORS["accent"], font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, padding=20)
        root_frame.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(root_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            header_frame,
            text="ZAPRET CONTROL",
            font=("Segoe UI", 24, "bold"),
            foreground=COLORS["accent"]
        ).pack(side="left")

        self.status_label = tk.Label(
            header_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["secondary_bg"],
            fg=COLORS["warning"],
            padx=15,
            pady=5,
            relief="flat"
        )
        self.status_label.pack(side="right")

        # Main Actions
        actions_card = ttk.LabelFrame(root_frame, text="Управление сервисом", padding=15)
        actions_card.pack(fill="x", pady=(0, 20))

        btn_container = ttk.Frame(actions_card)
        btn_container.pack(fill="x")

        ttk.Button(btn_container, text="▶ Запустить", style="Accent.TButton", command=self.start_service).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(btn_container, text="⏹ Остановить", command=self.stop_service).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(btn_container, text="🔄 Перезапустить", command=self.restart_service).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(btn_container, text="↻ Обновить статус", command=self.show_status).pack(side="left", expand=True, fill="x", padx=5)

        # Content Split (Status Details & Blockcheck)
        content_frame = ttk.Frame(root_frame)
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=1, minsize=400)
        content_frame.columnconfigure(1, weight=1, minsize=400)
        content_frame.rowconfigure(0, weight=1)

        # Left: System Status Details
        details_frame = ttk.LabelFrame(content_frame, text="Подробный статус системы", padding=10)
        details_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.status_text = tk.Text(details_frame, bg="#121212", fg="#00ff00", 
                                   insertbackground="white", font=("Consolas", 10),
                                   relief="flat", borderwidth=0, padx=10, pady=10)
        self.status_text.pack(fill="both", expand=True)
        self.status_text.configure(state="disabled")

        # Right: Blockcheck
        block_frame = ttk.LabelFrame(content_frame, text="Проверка блокировок (blockcheck.sh)", padding=10)
        block_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        ttk.Label(block_frame, text="Ответы для скрипта (каждый с новой строки):", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        
        self.input_text = tk.Text(block_frame, bg=COLORS["secondary_bg"], fg=COLORS["fg"],
                                  insertbackground="white", font=("Consolas", 10),
                                  relief="flat", height=8, padx=10, pady=10)
        self.input_text.pack(fill="x", pady=(0, 10))

        block_btn_frame = ttk.Frame(block_frame)
        block_btn_frame.pack(fill="x")
        ttk.Button(block_btn_frame, text="🚀 Запустить blockcheck", style="Accent.TButton", command=self.run_blockcheck).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Button(block_btn_frame, text="🗑 Очистить", command=self.clear_input).pack(side="left", padx=(5, 0))

        # Bottom: Logs
        log_frame = ttk.LabelFrame(root_frame, text="Журнал событий", padding=10)
        log_frame.pack(fill="both", expand=False, pady=(20, 0))
        
        self.log_text = tk.Text(log_frame, bg="#121212", fg="#cccccc", 
                                 height=6, font=("Consolas", 9),
                                 relief="flat", borderwidth=0, padx=10, pady=5)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

        # Footer
        footer_frame = ttk.Frame(root_frame)
        footer_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(footer_frame, textvariable=self.terminal_var, font=("Segoe UI", 8), foreground="#666666").pack(side="left")
        ttk.Label(footer_frame, text="v1.2 Enhanced", font=("Segoe UI", 8), foreground="#666666").pack(side="right")

        self.log("Приложение запущено с улучшенным интерфейсом.")

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{tk.datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_input(self) -> None:
        self.input_text.delete("1.0", "end")

    def _detect_terminal(self) -> list[str] | None:
        terminals = [
            ["x-terminal-emulator", "-e"],
            ["gnome-terminal", "--", "bash", "-lc"],
            ["konsole", "-e", "bash", "-lc"],
            ["xfce4-terminal", "--command"],
            ["xterm", "-e"],
        ]
        for cmd in terminals:
            if shutil.which(cmd[0]):
                return cmd
        return None

    def run_in_terminal(self, command: str, action: str) -> None:
        terminal_cmd = self.detected_terminal or self._detect_terminal()
        if not terminal_cmd:
            messagebox.showerror("Ошибка", "Не найден поддерживаемый терминал.")
            self.log(f"ERROR: {action} - терминал не найден")
            return

        wrapped = f"{command}; echo; read -p 'Нажмите Enter для закрытия...' _"
        if terminal_cmd[0] in {"x-terminal-emulator", "xterm", "xfce4-terminal"}:
            full_cmd = terminal_cmd + ["bash -lc " + shlex.quote(wrapped)]
        else:
            full_cmd = terminal_cmd + [wrapped]

        self.log(f"RUN: {action}")
        try:
            subprocess.Popen(full_cmd)
        except Exception as exc:
            messagebox.showerror("Ошибка", f"{action} не выполнено: {exc}")
            self.log(f"ERROR: {action} - {exc}")

    def start_service(self) -> None:
        self.run_in_terminal(f"sudo systemctl start {SERVICE_NAME}", "Запуск сервиса")

    def stop_service(self) -> None:
        self.run_in_terminal(f"sudo systemctl stop {SERVICE_NAME}", "Остановка сервиса")

    def restart_service(self) -> None:
        self.run_in_terminal(f"sudo systemctl restart {SERVICE_NAME}", "Перезапуск сервиса")

    def run_blockcheck(self) -> None:
        raw_input = self.input_text.get("1.0", "end").strip()
        if raw_input:
            payload = raw_input + "\n"
            quoted_payload = shlex.quote(payload)
            cmd = f"cd ~/zapret && printf %s {quoted_payload} | sudo ./blockcheck.sh"
            self.log(f"INFO: Передано строк в blockcheck: {len(raw_input.splitlines())}")
        else:
            cmd = "cd ~/zapret && sudo ./blockcheck.sh"
            self.log("INFO: blockcheck запущен без подготовленного ввода")

        self.run_in_terminal(cmd, "Запуск blockcheck")

    def _run_status_command(self) -> tuple[str, str]:
        commands = [
            ["sudo", "-n", "systemctl", "status", SERVICE_NAME, "--no-pager"],
            ["systemctl", "status", SERVICE_NAME, "--no-pager"],
        ]
        for cmd in commands:
            try:
                result = subprocess.run(cmd, check=False, capture_output=True, text=True)
                output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
                if output.strip():
                    return output.strip(), " ".join(cmd)
            except:
                continue
        return "Не удалось получить вывод systemctl status.", "systemctl status"

    def load_status_details(self) -> None:
        try:
            output, used_cmd = self._run_status_command()
            self._set_text(self.status_text, output)
        except Exception as exc:
            self._set_text(self.status_text, f"Ошибка чтения статуса: {exc}")

    def refresh_status(self) -> None:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", SERVICE_NAME],
                check=False,
                capture_output=True,
                text=True,
            )
            state = result.stdout.strip().lower()
        except Exception as exc:
            self.status_var.set("Состояние: ошибка")
            self.status_label.configure(fg=COLORS["danger"])
            return

        if state == "active":
            self.status_var.set("● СЕРВИС АКТИВЕН")
            self.status_label.configure(fg=COLORS["success"])
        else:
            self.status_var.set("○ СЕРВИС ОСТАНОВЛЕН")
            self.status_label.configure(fg=COLORS["danger"])

    def show_status(self) -> None:
        self.refresh_status()
        self.load_status_details()
        self.log("Статус обновлен.")

def main() -> None:
    root = tk.Tk()
    # Фикс для datetime в log()
    import datetime
    tk.datetime = datetime
    ZapretControlApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
