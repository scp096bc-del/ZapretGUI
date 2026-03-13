import tkinter as tk
from zapret_gui_new import ZapretControlApp
import os

# Подменяем subprocess.run и Popen, чтобы не вызывать реальные команды в песочнице
import subprocess
def mock_run(*args, **kwargs):
    class MockResult:
        stdout = "active"
        stderr = ""
        def strip(self): return self.stdout
    return MockResult()

def mock_popen(*args, **kwargs):
    pass

subprocess.run = mock_run
subprocess.Popen = mock_popen

def take_screenshot():
    root = tk.Tk()
    import datetime
    tk.datetime = datetime
    app = ZapretControlApp(root)
    
    # Эмулируем заполнение данных
    app._set_text(app.status_text, "● zapret.service - zapret service\n   Loaded: loaded (/etc/systemd/system/zapret.service; enabled; vendor preset: enabled)\n   Active: active (running) since Fri 2026-03-13 12:00:00 UTC; 10min ago\n Main PID: 1234 (nfqws)\n    Tasks: 1 (limit: 4915)\n   Memory: 2.5M\n   CGroup: /system.slice/zapret.service\n           └─1234 /usr/bin/nfqws --dpi-desync=fake,split2")
    app.log("Пример лога: сервис успешно запущен.")
    app.log("Пример лога: проверка блокировок завершена.")
    
    root.update()
    
    # В песочнице нет GUI сервера, поэтому мы не можем реально сделать скриншот через tk
    # Но мы можем сохранить код и сообщить пользователю об изменениях.
    # Для демонстрации я просто завершу выполнение.
    root.destroy()

if __name__ == "__main__":
    take_screenshot()
