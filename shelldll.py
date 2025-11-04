import os
import subprocess
import shutil
import psutil
from datetime import datetime
import platform
from prettytable import PrettyTable
from colorama import Fore, init
from art import tprint
import threading
import http.server
import socketserver
import webbrowser
import signal
import time
import json

init(autoreset=True)

LOG_DIR = "log"
DATA_LOG = os.path.join(LOG_DIR, "data.log")
API_LOG = os.path.join(LOG_DIR, "api.log")
WEB_LOG = os.path.join(LOG_DIR, "web.log")
KERNEL_LOG = "kernelLog.log"
SWAGGER_FLAG = "swagger.flag"     
WEB_PID_FILE = "web_server.pid"
WEB_SITE_DIR = "site"

os.makedirs(LOG_DIR, exist_ok=True)


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_event(message: str):
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = f"[{now_str()}] {message}\n"
    with open(DATA_LOG, "a", encoding="utf-8") as f:
        f.write(entry)
    with open(API_LOG, "a", encoding="utf-8") as f:
        f.write(entry)

def log_web(message: str):
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = f"[{now_str()}] {message}\n"
    with open(WEB_LOG, "a", encoding="utf-8") as f:
        f.write(entry)
    with open(DATA_LOG, "a", encoding="utf-8") as f:
        f.write(entry)

def safe_print_table(headers, rows):
    table = PrettyTable(headers)
    for r in rows:
        table.add_row(r)
    print(table)

_httpd_process = None
_httpd_thread = None

class SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        msg = f"{self.client_address[0]} - {format % args}"
        log_web(msg)

def _start_http_server_thread(host="0.0.0.0", port=8080, directory=WEB_SITE_DIR):
    os.makedirs(directory, exist_ok=True)
    handler_class = SilentHandler
    try:
        handler = lambda *args, **kwargs: handler_class(*args, directory=directory, **kwargs)
    except TypeError:
        handler = handler_class
        os.chdir(directory)
    with socketserver.TCPServer((host, port), handler) as httpd:
        log_web(f"[web] Start HTTP server on {host}:{port}, serving '{directory}'")
        with open(WEB_PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            log_web("[web] HTTP server stopped")
            if os.path.exists(WEB_PID_FILE):
                try:
                    os.remove(WEB_PID_FILE)
                except Exception:
                    pass

def cmd_web_start():
    global _httpd_thread
    if _httpd_thread and _httpd_thread.is_alive():
        print(Fore.YELLOW + "⚠️ Веб-сервер уже запущен." + Fore.RESET)
        return
    host = "0.0.0.0"
    port = 8080
    _httpd_thread = threading.Thread(target=_start_http_server_thread, args=(host, port, WEB_SITE_DIR), daemon=True)
    _httpd_thread.start()
    time.sleep(0.5)
    print(Fore.GREEN + f"🚀 Веб-сервер запущен на http://{host}:{port}, раздаётся папка '{WEB_SITE_DIR}'" + Fore.RESET)
    log_event(f"[shell] Запущен веб-сервер ({host}:{port}) -> {WEB_SITE_DIR}")

def cmd_web_stop():
    if os.path.exists(WEB_PID_FILE):
        try:
            with open(WEB_PID_FILE, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())
            if pid == os.getpid():
                print(Fore.YELLOW + "⚠️ Веб-сервер запущен как поток в этом процессе — перезапустите shell, чтобы остановить его, или закройте приложение." + Fore.RESET)
            else:
                try:
                    os.kill(pid, signal.SIGTERM)
                    print(Fore.GREEN + f"✅ Остановлен процесс веб-сервера (PID {pid})" + Fore.RESET)
                    log_event(f"[shell] Остановлен веб-сервер (PID {pid})")
                except Exception as e:
                    print(Fore.RED + f"❌ Не удалось убить процесс {pid}: {e}" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + f"❌ Ошибка при чтении {WEB_PID_FILE}: {e}" + Fore.RESET)
        try:
            os.remove(WEB_PID_FILE)
        except Exception:
            pass
    else:
        killed = 0
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = " ".join(proc.info.get("cmdline") or [])
                if "http.server" in cmdline or "SimpleHTTPServer" in cmdline:
                    proc.kill()
                    killed += 1
            except Exception:
                continue
        if killed:
            print(Fore.GREEN + f"✅ Остановлено {killed} веб-процесс(ов)." + Fore.RESET)
            log_event(f"[shell] Остановлено {killed} веб-процесс(ов)")
        else:
            print(Fore.YELLOW + "⚠️ Веб-сервер не найден." + Fore.RESET)

def cmd_web_open():
    index_path = os.path.join(WEB_SITE_DIR, "index.html")
    if os.path.exists(index_path):
        url = "http://127.0.0.1:8080/"
        try:
            webbrowser.open(url)
            print(Fore.GREEN + f"🌐 Открываю {url}" + Fore.RESET)
            log_event("[shell] Opened site in browser")
        except Exception as e:
            print(Fore.RED + f"❌ Не удалось открыть браузер: {e}" + Fore.RESET)
    else:
        print(Fore.RED + "❌ index.html не найден в папке site/. Используй $web find" + Fore.RESET)

def cmd_web_find():
    found = []
    for root, dirs, files in os.walk("."):
        if "index.html" in files:
            found.append(os.path.join(root, "index.html"))
    if not found:
        print(Fore.YELLOW + "🔎 index.html не найден." + Fore.RESET)
    else:
        print(Fore.CYAN + "Найденные index.html:" + Fore.RESET)
        for p in found:
            print(" -", os.path.normpath(p))
        log_event(f"[shell] Найдены index.html: {found}")

def cmd_web_log():
    if os.path.exists(WEB_LOG):
        print(Fore.CYAN + f"📜 Логи веб-сервера ({WEB_LOG}):" + Fore.RESET)
        print("-" * 60)
        with open(WEB_LOG, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for line in lines[-200:]:
                print(line.rstrip())
        print("-" * 60)
    else:
        print(Fore.YELLOW + "⚠️ Веб-лог ещё не создан." + Fore.RESET)

def cmd_site_info():
    path = WEB_SITE_DIR
    if not os.path.exists(path):
        print(Fore.RED + f"❌ Папка сайта '{path}' не найдена." + Fore.RESET)
        return
    file_count = 0
    folder_count = 0
    total_size = 0
    for root, dirs, files in os.walk(path):
        file_count += len(files)
        folder_count += len(dirs)
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    print(Fore.MAGENTA + f"🖼 Информация о папке '{path}':" + Fore.RESET)
    print(f"Файлов: {file_count}\nПапок: {folder_count}\nОбщий размер: {round(total_size / (1024 ** 2), 2)} МБ")
    log_event(f"[shell] Просмотр папки site/ (files={file_count}, size_mb={round(total_size / (1024**2),2)})")

def cmd_site_clear():
    path = WEB_SITE_DIR
    if not os.path.exists(path):
        print(Fore.RED + f"❌ Папка сайта '{path}' не найдена." + Fore.RESET)
        return
    removed = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith(".tmp") or f.endswith(".cache") or f.endswith(".bak"):
                try:
                    os.remove(os.path.join(root, f))
                    removed += 1
                except Exception:
                    continue
    print(Fore.GREEN + f"🧹 Очищено {removed} временных файлов в '{path}'" + Fore.RESET)
    log_event(f"[shell] Очистка сайта: удалено {removed} временных файлов")


def cmd_swagger_on():
    try:
        with open(SWAGGER_FLAG, "w", encoding="utf-8") as f:
            f.write("on")
        print(Fore.GREEN + "✅ Swagger включен (флаг установлен ON). Перезапустите API чтобы изменения вступили в силу." + Fore.RESET)
        log_event("[shell] Swagger flag set: on")
    except Exception as e:
        print(Fore.RED + f"❌ Ошибка при установке флага: {e}" + Fore.RESET)

def cmd_swagger_off():
    try:
        with open(SWAGGER_FLAG, "w", encoding="utf-8") as f:
            f.write("off")
        print(Fore.YELLOW + "⚠️ Swagger отключен (флаг установлен OFF). Перезапустите API чтобы изменения вступили в силу." + Fore.RESET)
        log_event("[shell] Swagger flag set: off")
    except Exception as e:
        print(Fore.RED + f"❌ Ошибка при установке флага: {e}" + Fore.RESET)

def cmd_swagger_status():
    status = "unknown"
    if os.path.exists(SWAGGER_FLAG):
        try:
            with open(SWAGGER_FLAG, "r", encoding="utf-8") as f:
                status = f.read().strip()
        except Exception:
            status = "error"
    print(Fore.CYAN + f"Swagger flag: {status}" + Fore.RESET)

def cmd_get_users():
    try:
        from databasedll import users_collection
    except Exception as e:
        print(Fore.RED + f"❌ Не удалось подключиться к users_collection: {e}" + Fore.RESET)
        log_event(f"[shell] Ошибка подключения к users_collection: {e}")
        return
    try:
        rows = []
        cursor = users_collection.find({}, {"username": 1, "usernick": 1, "_id": 0}).limit(100)
        for u in cursor:
            rows.append([u.get("username", ""), u.get("usernick", "")])
        if rows:
            safe_print_table(["username", "usernick"], rows)
        else:
            print(Fore.YELLOW + "📭 Пользователи не найдены." + Fore.RESET)
    except Exception as e:
        print(Fore.RED + f"❌ Ошибка при получении юзеров: {e}" + Fore.RESET)
        log_event(f"[shell] Ошибка получения юзеров: {e}")

def cmd_db_stats():
    try:
        from databasedll import db
        stats = db.command("dbstats")
        rows = [
            ["collections", stats.get("collections")],
            ["objects", stats.get("objects")],
            ["avgObjSize", stats.get("avgObjSize")],
            ["dataSize", stats.get("dataSize")],
            ["storageSize", stats.get("storageSize")]
        ]
        safe_print_table(["Метрика", "Значение"], rows)
        log_event("[shell] Получена статистика БД")
    except Exception as e:
        print(Fore.RED + f"❌ Не удалось получить статистику БД: {e}" + Fore.RESET)
        log_event(f"[shell] Ошибка db stats: {e}")

def cmd_log_tail(lines=50):
    if os.path.exists(DATA_LOG):
        with open(DATA_LOG, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                print(line.rstrip())
    else:
        print(Fore.YELLOW + "⚠️ data.log не найден." + Fore.RESET)

def cmd_reset_logs():
    for p in [DATA_LOG, API_LOG, WEB_LOG, KERNEL_LOG]:
        try:
            if os.path.exists(p):
                open(p, "w", encoding="utf-8").close()
        except Exception:
            pass
    print(Fore.GREEN + "✅ Все логи очищены." + Fore.RESET)
    log_event("[shell] Логи очищены")

def cmd_get_config():
    cfg_file = "dataApi.txt"
    if not os.path.exists(cfg_file):
        print(Fore.RED + f"❌ Конфиг {cfg_file} не найден." + Fore.RESET)
        return
    print(Fore.CYAN + f"Конфиг {cfg_file}:" + Fore.RESET)
    with open(cfg_file, "r", encoding="utf-8") as f:
        for line in f:
            print(line.rstrip())

def cmd_status():
    status = []
    uvicorn_found = False
    web_found = False
    mongo_found = False
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info.get("cmdline") or [])
            if "uvicorn" in cmdline:
                uvicorn_found = True
            if "http.server" in cmdline or "SimpleHTTPServer" in cmdline:
                web_found = True
            if "mongod" in cmdline:
                mongo_found = True
        except Exception:
            continue
    status.append(["uvicorn (API)", "running" if uvicorn_found else "stopped"])
    status.append(["web server", "running" if web_found or (os.path.exists(WEB_PID_FILE)) else "stopped"])
    status.append(["mongod", "running" if mongo_found else "stopped"])
    safe_print_table(["Service", "Status"], status)
    log_event("[shell] checked status")

def cmd_get_api_log_tail():
    if os.path.exists(API_LOG):
        with open(API_LOG, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for line in lines[-200:]:
                print(line.rstrip())
    else:
        print(Fore.YELLOW + "⚠️ api.log не найден." + Fore.RESET)

def cmd_log_filter_error():
    if os.path.exists(DATA_LOG):
        with open(DATA_LOG, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "ERROR" in line.upper() or "❌" in line or "WARNING" in line.upper() or "⚠️" in line:
                    print(line.rstrip())
    else:
        print(Fore.YELLOW + "⚠️ data.log не найден." + Fore.RESET)

def cmd_get_commands_md():
    md_path = "commands.md"
    commands_info = {
        "$get system-info": "Показать системную информацию",
        "$set": "Запустить API сервер (uvicorn) в отдельном процессе",
        "$get api-log": "Показать лог API сервера",
        "$get api-log-save": "Сохранить резервную копию лога API",
        "$get server-info": "Показать нагрузку и адрес",
        "$stop server": "Аварийно остановить сервер",
        "$restart server": "Перезапустить сервер",
        "$restart pc": "Перезагрузить компьютер",
        "$get folder-info": "Информация о папке",
        "$get image-info": "Информация о папке image",
        "$exit": "Выйти из shell",
        "$info": "Показать информацию о версии",
        "$swagger on": "Включить Swagger (установить флаг ON)",
        "$swagger off": "Отключить Swagger (установить флаг OFF)",
        "$swagger status": "Показать текущее состояние флага Swagger",
        "$web start": "Запустить статический веб-сервер для папки site/",
        "$web stop": "Остановить статический веб-сервер",
        "$web open": "Открыть сайт в браузере (если есть index.html)",
        "$web find": "Найти index.html в проекте",
        "$web log": "Показать лог веб-сервера",
        "$site info": "Показать статистику папки site/",
        "$site clear": "Очистить временные файлы в site/",
        "$get users": "Показать пользователей (username, usernick)",
        "$db stats": "Показать статистику MongoDB",
        "$log tail": "Показать последние строки data.log",
        "$log filter error": "Показать ошибки/предупреждения в логах",
        "$status": "Проверить статусы сервисов",
        "$get config": "Показать содержимое dataApi.txt",
        "$reset logs": "Очистить логи",
        "$get commands": "Создать commands.md (этот файл)"
    }
    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# TreeHub Shell - Commands\n\n")
            for cmd, desc in commands_info.items():
                f.write(f"- `{cmd}` — {desc}\n")
        print(Fore.GREEN + f"✅ Файл {md_path} создан." + Fore.RESET)
        log_event("[shell] commands.md создан")
    except Exception as e:
        print(Fore.RED + f"❌ Ошибка при создании {md_path}: {e}" + Fore.RESET)

def cmd_update_shell():
    print(Fore.YELLOW + "🔄 Проверка обновлений: функционал пока заглушка." + Fore.RESET)
    log_event("[shell] update check (stub)")


def cmd_get_system_info():
    try:
        from system_info import get_system_info
        log_event("[shell] Запрос на $get system-info")
        print(get_system_info())
    except Exception as e:
        print(Fore.RED + f"❌ Ошибка при получении системной информации: {e}" + Fore.RESET)
        log_event(f"[shell] system-info error: {e}")

def cmd_set_server():
    """Запускает API сервер в отдельном процессе (uvicorn serverdll:server)."""
    now = now_str()
    print("Запуск API сервера! Предупреждаем, что будет включен IP сервер, смотрите настройки NGINX")
    if not os.path.exists("serverdll.py"):
        print(Fore.RED + "Компонент API, serverdll.py не найден" + Fore.RESET)
        return
    log_event(f"[{now}] [shell] Запуск API сервера")
    host = "0.0.0.0"
    port = 8000
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"🚀 TreeHub API запущен на {host}:{port}")
    print("🟢 Для остановки нажмите CTRL+C")
    with open(API_LOG, "a", encoding="utf-8") as log_file:
        try:
            subprocess.Popen(
                ["python", "-m", "uvicorn", "serverdll:server", "--host", host, "--port", str(port), "--log-level", "info"],
                stdout=log_file,
                stderr=log_file,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            print(Fore.GREEN + "🌿 Сервер запущен в отдельном процессе." + Fore.RESET)
            log_event("[shell] uvicorn subprocess started")
        except Exception as e:
            print(Fore.RED + f"❌ Ошибка при запуске uvicorn: {e}" + Fore.RESET)
            log_event(f"[shell] uvicorn start failed: {e}")

def cmd_get_api_log():
    if os.path.exists(API_LOG):
        print(Fore.GREEN + f"📜 Логи API сервера ({API_LOG}):" + Fore.RESET)
        print("-" * 60)
        with open(API_LOG, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            if not lines:
                print(Fore.YELLOW + "Лог сервера пуст!" + Fore.RESET)
            else:
                for line in lines[-200:]:
                    print(line.strip())
        print("-" * 60)
    else:
        print(Fore.RED + "⚠️ Лог сервера ещё не создан (сервер, возможно, не запущен)" + Fore.RESET)

def cmd_save_api_log():
    if os.path.exists(API_LOG):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"log/api_backup_{now}.log"
        shutil.copy(API_LOG, backup_name)
        print(Fore.GREEN + f"✅ Лог API сохранён как {backup_name}" + Fore.RESET)
        log_event(f"[shell] Резервная копия api.log -> {backup_name}")
    else:
        print(Fore.RED + "⚠️ Лог сервера не найден!" + Fore.RESET)

def cmd_server_info():
    host = "0.0.0.0"
    port = 8000
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    print(Fore.CYAN + "📡 Информация о сервере:" + Fore.RESET)
    table = PrettyTable(["Параметр", "Значение"])
    table.add_row(["Адрес", host])
    table.add_row(["Порт", port])
    table.add_row(["Загрузка CPU", f"{cpu}%"])
    table.add_row(["Использование RAM", f"{ram}%"])
    print(table)
    log_event(f"[shell] Просмотр информации о сервере ({host}:{port})")

def cmd_stop_server():
    killed = 0
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["cmdline"] and "uvicorn" in " ".join(proc.info["cmdline"]):
                proc.kill()
                killed += 1
        except Exception:
            continue
    if killed:
        print(Fore.RED + f"⛔ Сервер аварийно остановлен ({killed} процесс(ов))" + Fore.RESET)
        log_event("[shell] Аварийная остановка сервера")
    else:
        print(Fore.YELLOW + "⚠️ Сервер не найден среди активных процессов." + Fore.RESET)

def cmd_restart_server():
    print(Fore.YELLOW + "🔄 Перезапуск сервера..." + Fore.RESET)
    cmd_stop_server()
    cmd_set_server()
    log_event("[shell] Перезапуск сервера выполнен")

def cmd_restart_pc():
    print(Fore.RED + "⚠️ Внимание! ПК будет перезагружен через 3 секунды..." + Fore.RESET)
    log_event("[shell] Инициирована перезагрузка ПК")
    if os.name == "nt":
        os.system("shutdown /r /t 3")
    else:
        os.system("sudo reboot")

def cmd_folder_info():
    path = input(Fore.CYAN + "Введите путь к папке: " + Fore.RESET).strip()
    if not os.path.exists(path):
        print(Fore.RED + "❌ Указанная папка не найдена!" + Fore.RESET)
        return
    file_count = 0
    folder_count = 0
    total_size = 0
    for root, dirs, files in os.walk(path):
        file_count += len(files)
        folder_count += len(dirs)
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    print(Fore.GREEN + f"📂 Информация о папке: {path}" + Fore.RESET)
    print(f"Файлов: {file_count}")
    print(f"Папок: {folder_count}")
    print(f"Общий размер: {round(total_size / (1024 ** 2), 2)} МБ")
    log_event(f"[shell] Проверена папка: {path}")

def cmd_image_info():
    path = "image"
    if not os.path.exists(path):
        print(Fore.RED + "⚠️ Папка 'image' не найдена!" + Fore.RESET)
        return
    file_count = 0
    folder_count = 0
    total_size = 0
    for root, dirs, files in os.walk(path):
        file_count += len(files)
        folder_count += len(dirs)
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    print(Fore.MAGENTA + f"🖼 Информация о папке 'image':" + Fore.RESET)
    print(f"Файлов: {file_count}")
    print(f"Папок: {folder_count}")
    print(f"Общий размер: {round(total_size / (1024 ** 2), 2)} МБ")
    log_event("[shell] Просмотр папки image/")

def cmd_exit():
    print(Fore.CYAN + "Завершение работы TreeHub Shell..." + Fore.RESET)
    log_event("[shell] Завершение сеанса пользователя")
    exit(0)

def unknown_command():
    print(Fore.YELLOW + "Неизвестная команда! Используй:" + Fore.RESET)
    print("""
    $get system-info    — показать системную информацию
    $set                — запустить сервер
    $get api-log        — показать логи сервера
    $get api-log-save   — сохранить лог API
    $get server-info    — нагрузка и адрес
    $stop server        — аварийно остановить сервер
    $restart server     — перезапустить сервер
    $restart pc         — перезагрузить компьютер
    $get folder-info    — информация о папке
    $get image-info     — информация о папке image
    $exit               — выйти из shell
    Доп. команды:
    $swagger on/off/status
    $web start/stop/open/find/log
    $site info/clear
    $get users
    $db stats
    $log tail
    $log filter error
    $status
    $get config
    $reset logs
    $get commands
    """)

def info():
    tprint("TreeHub API")
    tprint("Generation 1")
    print("""
      TreeHub Professional 2025
      Version: 1.0.0
      Made in Python
      GitHub: https://github.com/DKhorov/TreeHub.git
    """)


commands = {
    "$get system-info": cmd_get_system_info,
    "$set": cmd_set_server,
    "$get api-log": cmd_get_api_log,
    "$get api-log-save": cmd_save_api_log,
    "$get server-info": cmd_server_info,
    "$stop server": cmd_stop_server,
    "$restart server": cmd_restart_server,
    "$restart pc": cmd_restart_pc,
    "$get folder-info": cmd_folder_info,
    "$get image-info": cmd_image_info,
    "$exit": cmd_exit,
    "$info": info,
    "$swagger on": cmd_swagger_on,
    "$swagger off": cmd_swagger_off,
    "$swagger status": cmd_swagger_status,
    "$web start": cmd_web_start,
    "$web stop": cmd_web_stop,
    "$web open": cmd_web_open,
    "$web find": cmd_web_find,
    "$web log": cmd_web_log,
    "$site info": cmd_site_info,
    "$site clear": cmd_site_clear,
    "$get users": cmd_get_users,
    "$db stats": cmd_db_stats,
    "$log tail": cmd_log_tail,
    "$log filter error": cmd_log_filter_error,
    "$status": cmd_status,
    "$get config": cmd_get_config,
    "$reset logs": cmd_reset_logs,
    "$get commands": cmd_get_commands_md,
    "$update shell": cmd_update_shell,
    "$get api-log-tail": cmd_get_api_log_tail
}

# ---- Shell loop ----
def shell():
    print("TreeHub Shell v3.0 - Python", platform.python_version(), "OpenSource")
    # приветственное сообщение
    info()
    while True:
        try:
            now = datetime.now()
            console_input = input("> ").strip()
            if not console_input:
                continue
            # поддержка аргументов: allow commands like "$log tail 100"
            # разделим команду и args
            parts = console_input.split()
            base = " ".join(parts[:2]) if " ".join(parts[:2]) in commands else parts[0]
            cmd = commands.get(base, None)
            if cmd:
                # передача числового аргумента для некоторых команд
                if base in ("$log tail",) and len(parts) >= 3:
                    try:
                        n = int(parts[2])
                    except:
                        n = 50
                    cmd(n)
                else:
                    cmd()
            else:
                unknown_command()
        except KeyboardInterrupt:
            print()
            print(Fore.YELLOW + "Прерывание клавиатурой. Используй $exit для выхода." + Fore.RESET)
        except Exception as e:
            print(Fore.RED + f"Ошибка в shell: {e}" + Fore.RESET)
            log_event(f"[shell] exception: {e}")

# TreeHub API - Source Code
# This language is Python
# This file is: shelldll.py
# Author: Dmitry Khorov
# GitHub: https://github.com/DKhorov/TreeHub.git
