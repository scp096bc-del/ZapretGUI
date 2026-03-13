# Zapret Control GUI (Linux) - v1.2 Enhanced

GUI-программа для управления сервисом `zapret` с установкой через `.deb`. Теперь с современным темным интерфейсом!

## Возможности

- **Современный Dark Mode**: Улучшенный визуальный стиль для комфортной работы.
- **Индикация статуса**: Цветовая индикация состояния сервиса (активен/остановлен).
- **Start zapret** — запускает в терминале:
   - `sudo systemctl start zapret`
2. **Stop zapret** — запускает:
   - `sudo systemctl stop zapret`
3. **Restart zapret** — запускает:
   - `sudo systemctl restart zapret`
4. **blockcheck.sh + поле ввода** — запускает:
   - `cd ~/zapret && sudo ./blockcheck.sh`
   - ответы из окна ввода (много строк) отправляются в stdin скрипта
5. **Status zapret** — выводит в приложение:
   - понятный статус `active` или `stopped`
   - подробный вывод `systemctl status zapret` в отдельном блоке GUI

## Запуск из исходников

```bash
python3 zapret_gui.py
```

## Сборка .deb

```bash
./packaging/build_deb.sh
```

Пакет будет в папке `dist/`.

## Сборка релиза

```bash
./release/build_release.sh
```

В папке `release/` будут:
- `zapret-control_1.1.0_all.deb`
- `zapret-control_1.1.0_all.deb.sha256`
- `RELEASE_NOTES_1.1.0.md`

## Установка .deb

```bash
sudo dpkg -i release/zapret-control_1.1.0_all.deb
sudo apt-get -f install -y
```

Запуск после установки:

```bash
zapret-control
```

или через меню приложений (**Zapret Control**).

## Зависимости

- Linux
- Python 3
- `python3-tk`
- `dpkg-deb` (для сборки `.deb`)
- терминал (`x-terminal-emulator`, `gnome-terminal`, `konsole`, `xfce4-terminal` или `xterm`)
- права `sudo` для команд управления сервисом
