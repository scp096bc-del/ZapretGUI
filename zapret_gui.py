#!/usr/bin/env python3
import shlex
import shutil
import subprocess
import datetime
import threading
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

APP_TITLE = "Zapret Control"
SERVICE_NAME = "zapret"

# Цветовая схема (Modern Dark Theme)
COLORS = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "accent": "#0078d4",
    "secondary_bg": "#2d2d2d",
    "border": "#3f3f3f",
    "success": "#28a745",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#17a2b8",
    "terminal_bg": "#0c0c0c",
    "terminal_fg": "#00ff00"
}

def ensure_root():
    """Перезапуск скрипта с правами root, сохраняя X11 окружение."""
    if os.geteuid() != 0:
        args = [sys.executable] + sys.argv
        env = os.environ.copy()
        
        # Пытаемся сохранить DISPLAY и XAUTHORITY для корректного GUI под root
        display = env.get('DISPLAY')
        xauth = env.get('XAUTHORITY')
        
        try:
            if display:
                # Если pkexec доступен, используем его (он лучше работает с GUI)
                if shutil.which('pkexec'):
                    # pkexec по умолчанию очищает окружение, поэтому передаем DISPLAY явно через bash
                    cmd = ['pkexec', 'env', f'DISPLAY={display}']
                    if xauth:
                        cmd.append(f'XAUTHORITY={xauth}')
                    cmd.extend(args)
                    subprocess.check_call(cmd)
                else:
                    # Если нет pkexec, пробуем sudo -E (preserve environment)
                    subprocess.check_call(['sudo', '-E'] + args)
            else:
                # Если DISPLAY нет (запуск из консоли), обычный sudo
                subprocess.check_call(['sudo'] + args)
            sys.exit(0)
        except subprocess.CalledProcessError:
            # Пользователь отменил ввод пароля или произошла ошибка
            sys.exit(1)
        except Exception as e:
            print(f"Ошибка при попытке повышения прав: {e}")
            sys.exit(1)

class ZapretControlApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1000x800")
        self.root.minsize(900, 750)
        self.root.configure(bg=COLORS["bg"])

        self.status_var = tk.StringVar(value="Состояние: неизвестно")
        self.blockcheck_running = False
        self.process = None
        
        self._setup_styles()
        self._build_ui()
        
        self.refresh_status()
        self.load_status_details()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["fg"])
        style.configure("Accent.TButton", background=COLORS["accent"], foreground="white", font=("Segoe UI", 10, "bold"), padding=(10, 5))
        style.map("Accent.TButton", background=[("active", "#005a9e")])
        style.configure("TButton", background=COLORS["secondary_bg"], foreground=COLORS["fg"], padding=(10, 5))
        style.map("TButton", background=[("active", COLORS["border"])])
        style.configure("TLabelframe", background=COLORS["bg"], foreground=COLORS["fg"], bordercolor=COLORS["border"])
        style.configure("TLabelframe.Label", background=COLORS["bg"], foreground=COLORS["accent"], font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, padding=20)
        root_frame.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(root_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        ttk.Label(header_frame, text="ZAPRET CONTROL", font=("Segoe UI", 24, "bold"), foreground=COLORS["accent"]).pack(side="left")
        
        # Индикатор Root прав
        root_indicator = tk.Label(header_frame, text="ROOT ACCESS", font=("Segoe UI", 8, "bold"), bg=COLORS["success"], fg="white", padx=5)
        root_indicator.pack(side="left", padx=15)

        self.status_label = tk.Label(header_frame, textvariable=self.status_var, font=("Segoe UI", 11, "bold"), bg=COLORS["secondary_bg"], fg=COLORS["warning"], padx=15, pady=8, relief="flat", bd=0)
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

        # Content Split
        content_frame = ttk.Frame(root_frame)
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Left: System Status Details
        details_frame = ttk.LabelFrame(content_frame, text="Подробный статус системы", padding=10)
        details_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.status_text = tk.Text(details_frame, bg=COLORS["terminal_bg"], fg=COLORS["terminal_fg"], insertbackground="white", font=("Consolas", 10), relief="flat", borderwidth=0, padx=10, pady=10)
        self.status_text.pack(fill="both", expand=True)
        self.status_text.configure(state="disabled")

        # Right: Interactive Blockcheck
        block_frame = ttk.LabelFrame(content_frame, text="Интерактивная проверка", padding=10)
        block_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        self.block_terminal = tk.Text(block_frame, bg=COLORS["terminal_bg"], fg=COLORS["terminal_fg"], insertbackground="white", font=("Consolas", 10), relief="flat", borderwidth=0, padx=10, pady=10)
        self.block_terminal.pack(fill="both", expand=True)
        self.block_terminal.bind("<Return>", self._send_input_to_blockcheck)

        block_btn_frame = ttk.Frame(block_frame)
        block_btn_frame.pack(fill="x", pady=(10, 0))
        self.block_btn = ttk.Button(block_btn_frame, text="🚀 Запустить blockcheck", style="Accent.TButton", command=self.toggle_blockcheck)
        self.block_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Button(block_btn_frame, text="🗑 Очистить окно", command=self.clear_block_terminal).pack(side="left", padx=(5, 0))

        # Bottom: Logs
        log_frame = ttk.LabelFrame(root_frame, text="Журнал событий", padding=10)
        log_frame.pack(fill="both", expand=False, pady=(20, 0))
        self.log_text = tk.Text(log_frame, bg=COLORS["terminal_bg"], fg="#cccccc", height=6, font=("Consolas", 9), relief="flat", borderwidth=0, padx=10, pady=5)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

        # Footer
        footer_frame = ttk.Frame(root_frame)
        footer_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(footer_frame, text="v1.4.1 Fix-Launch", font=("Segoe UI", 8), foreground="#666666").pack(side="right")

        self.log("Приложение запущено от имени root. Все функции активны.")

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_block_terminal(self) -> None:
        self.block_terminal.delete("1.0", "end")

    def run_command_background(self, command: str, action: str):
        def task():
            self.log(f"RUN: {action}...")
            try:
                cmd_list = shlex.split(command.replace("sudo ", ""))
                process = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    self.log(f"SUCCESS: {action}")
                else:
                    self.log(f"ERROR: {action} (code {process.returncode}): {stderr.strip()}")
                self.root.after(500, self.show_status)
            except Exception as e:
                self.log(f"EXCEPTION: {action} - {e}")

        threading.Thread(target=task, daemon=True).start()

    def start_service(self) -> None: self.run_command_background(f"systemctl start {SERVICE_NAME}", "Запуск сервиса")
    def stop_service(self) -> None: self.run_command_background(f"systemctl stop {SERVICE_NAME}", "Остановка сервиса")
    def restart_service(self) -> None: self.run_command_background(f"systemctl restart {SERVICE_NAME}", "Перезапуск сервиса")

    def _run_status_command(self) -> str:
        cmd = ["systemctl", "status", SERVICE_NAME, "--no-pager"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip() or result.stderr.strip()

    def load_status_details(self) -> None:
        output = self._run_status_command()
        self._set_text(self.status_text, output)

    def refresh_status(self) -> None:
        try:
            result = subprocess.run(["systemctl", "is-active", SERVICE_NAME], capture_output=True, text=True)
            state = result.stdout.strip().lower()
            if state == "active":
                self.status_var.set("● СЕРВИС АКТИВЕН")
                self.status_label.configure(fg=COLORS["success"])
            else:
                self.status_var.set("○ СЕРВИС ОСТАНОВЛЕН")
                self.status_label.configure(fg=COLORS["danger"])
        except:
            self.status_var.set("○ ОШИБКА")
            self.status_label.configure(fg=COLORS["danger"])

    def show_status(self) -> None:
        self.refresh_status()
        self.load_status_details()

    def toggle_blockcheck(self):
        if self.blockcheck_running:
            self.stop_blockcheck()
        else:
            self.start_blockcheck()

    def start_blockcheck(self):
        self.blockcheck_running = True
        self.block_btn.configure(text="🛑 Остановить blockcheck", style="TButton")
        self.block_terminal.insert("end", ">>> Запуск blockcheck.sh...\n")
        self.block_terminal.see("end")
        
        def run():
            # Попытка найти путь к zapret пользователя, запустившего sudo
            sudo_user = os.environ.get('SUDO_USER')
            if sudo_user:
                zapret_path = os.path.join("/home", sudo_user, "zapret")
            else:
                zapret_path = os.path.expanduser("~/zapret")
            
            if not os.path.exists(zapret_path):
                self.block_terminal.insert("end", f"ОШИБКА: Директория {zapret_path} не найдена.\n")
                self.stop_blockcheck()
                return

            cmd = ["bash", "-c", f"cd {zapret_path} && ./blockcheck.sh"]
            try:
                self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                
                for line in iter(self.process.stdout.readline, ''):
                    if not self.blockcheck_running: break
                    self.block_terminal.insert("end", line)
                    self.block_terminal.see("end")
                
                self.process.wait()
                self.block_terminal.insert("end", f"\n>>> Проверка завершена (код {self.process.returncode})\n")
            except Exception as e:
                self.block_terminal.insert("end", f"\n>>> Ошибка: {e}\n")
            
            self.stop_blockcheck()

        threading.Thread(target=run, daemon=True).start()

    def stop_blockcheck(self):
        self.blockcheck_running = False
        if self.process:
            self.process.terminate()
        self.block_btn.configure(text="🚀 Запустить blockcheck", style="Accent.TButton")

    def _send_input_to_blockcheck(self, event):
        if self.blockcheck_running and self.process and self.process.poll() is None:
            line = self.block_terminal.get("insert linestart", "insert lineend")
            if line:
                self.process.stdin.write(line + "\n")
                self.process.stdin.flush()
                self.block_terminal.insert("end", "\n")
                return "break"

def main() -> None:
    ensure_root()
    root = tk.Tk()
    ZapretControlApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
