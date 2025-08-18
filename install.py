#!/usr/bin/env python3
"""
Скрипт установки Pyker
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_root():
    """Проверяет права root"""
    if os.geteuid() != 0:
        print("❌ Этот скрипт должен быть запущен с правами root (sudo)")
        sys.exit(1)

def install_dependencies():
    """Устанавливает системные зависимости"""
    print("📦 Установка системных зависимостей...")
    
    # Обновляем пакеты
    success, _, _ = run_command("apt update")
    if not success:
        print("⚠️  Не удалось обновить пакеты")
    
    # Устанавливаем Python и другие зависимости
    deps = [
        "python3",
        "python3-venv", 
        "python3-pip",
        "nodejs",
        "npm"
    ]
    
    for dep in deps:
        print(f"  Устанавливаем {dep}...")
        success, _, error = run_command(f"apt install -y {dep}")
        if not success:
            print(f"❌ Ошибка установки {dep}: {error}")
            return False
    
    return True

def create_directories():
    """Создает необходимые директории"""
    print("📁 Создание директорий...")
    
    directories = [
        "/opt/pyker",
        "/opt/pyker/scripts",
        "/opt/pyker/logs",
        "/var/log/pyker"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}")

def copy_files():
    """Копирует файлы в системные директории"""
    print("📋 Копирование файлов...")
    
    # Копируем основные файлы
    files_to_copy = [
        ("main.py", "/opt/pyker/"),
        ("requirements.txt", "/opt/pyker/"),
        ("pyker_cli.py", "/opt/pyker/"),
        ("pyker_web.py", "/opt/pyker/"),
        ("src/", "/opt/pyker/"),
        ("scripts/", "/opt/pyker/"),
        ("frontend/", "/opt/pyker/"),
        ("pyker.service", "/etc/systemd/system/")
    ]
    
    for src, dst in files_to_copy:
        if os.path.exists(src):
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            print(f"  ✅ {src} -> {dst}")
        else:
            print(f"  ⚠️  Файл не найден: {src}")

def setup_python_environment():
    """Настраивает Python окружение"""
    print("🐍 Настройка Python окружения...")
    
    # Создаем виртуальное окружение
    success, _, error = run_command("python3 -m venv venv", cwd="/opt/pyker")
    if not success:
        print(f"❌ Ошибка создания виртуального окружения: {error}")
        return False
    
    # Устанавливаем зависимости
    success, _, error = run_command("/opt/pyker/venv/bin/pip install -r requirements.txt", cwd="/opt/pyker")
    if not success:
        print(f"❌ Ошибка установки Python зависимостей: {error}")
        return False
    
    print("  ✅ Python окружение настроено")
    return True

def setup_frontend():
    """Настраивает фронтенд"""
    print("🌐 Настройка фронтенда...")
    
    frontend_dir = "/opt/pyker/frontend"
    
    # Устанавливаем npm зависимости
    success, _, error = run_command("npm install", cwd=frontend_dir)
    if not success:
        print(f"❌ Ошибка установки npm зависимостей: {error}")
        return False
    
    # Собираем фронтенд
    success, _, error = run_command("npm run build", cwd=frontend_dir)
    if not success:
        print(f"❌ Ошибка сборки фронтенда: {error}")
        return False
    
    print("  ✅ Фронтенд настроен")
    return True

def setup_cli():
    """Настраивает CLI команду"""
    print("🔧 Настройка CLI команды...")
    
    # Создаем символические ссылки
    cli_path = "/usr/local/bin/pyker"
    web_path = "/usr/local/bin/pyker-web"
    
    if os.path.exists(cli_path):
        os.remove(cli_path)
    if os.path.exists(web_path):
        os.remove(web_path)
    
    os.symlink("/opt/pyker/pyker_cli.py", cli_path)
    os.symlink("/opt/pyker/pyker_web.py", web_path)
    
    # Делаем исполняемыми
    os.chmod("/opt/pyker/pyker_cli.py", 0o755)
    os.chmod("/opt/pyker/pyker_web.py", 0o755)
    
    print("  ✅ CLI команда настроена")

def setup_systemd():
    """Настраивает systemd сервис"""
    print("⚙️  Настройка systemd сервиса...")
    
    # Перезагружаем systemd
    success, _, error = run_command("systemctl daemon-reload")
    if not success:
        print(f"❌ Ошибка перезагрузки systemd: {error}")
        return False
    
    # Включаем автозапуск
    success, _, error = run_command("systemctl enable pyker.service")
    if not success:
        print(f"❌ Ошибка включения автозапуска: {error}")
        return False
    
    print("  ✅ Systemd сервис настроен")
    return True

def set_permissions():
    """Устанавливает правильные права доступа"""
    print("🔐 Настройка прав доступа...")
    
    # Устанавливаем владельца
    run_command("chown -R root:root /opt/pyker")
    
    # Устанавливаем права
    run_command("chmod -R 755 /opt/pyker")
    run_command("chmod 644 /etc/systemd/system/pyker.service")
    
    print("  ✅ Права доступа настроены")

def main():
    print("🚀 Установка Pyker - Python Script Manager")
    print("=" * 50)
    
    # Проверяем права root
    check_root()
    
    # Устанавливаем зависимости
    if not install_dependencies():
        print("❌ Ошибка установки зависимостей")
        sys.exit(1)
    
    # Создаем директории
    create_directories()
    
    # Копируем файлы
    copy_files()
    
    # Настраиваем Python окружение
    if not setup_python_environment():
        print("❌ Ошибка настройки Python окружения")
        sys.exit(1)
    
    # Настраиваем фронтенд
    if not setup_frontend():
        print("❌ Ошибка настройки фронтенда")
        sys.exit(1)
    
    # Настраиваем CLI
    setup_cli()
    
    # Настраиваем systemd
    if not setup_systemd():
        print("❌ Ошибка настройки systemd")
        sys.exit(1)
    
    # Устанавливаем права
    set_permissions()
    
    print("\n🎉 Установка завершена!")
    print("=" * 50)
    print("📱 Веб-интерфейс: http://localhost:8000")
    print("🔌 API документация: http://localhost:8000/docs")
    print("📋 CLI команды:")
    print("  pyker start <name> <script>     # Запустить процесс (прямой режим)")
    print("  pyker list                      # Список процессов")
    print("  pyker logs <id>                 # Показать логи")
    print("  pyker stop <id>                 # Остановить процесс")
    print("  pyker restart <id>              # Перезапустить процесс")
    print("  pyker status                    # Статус")
    print("\n🌐 Веб-интерфейс:")
    print("  pyker-web                       # Запустить веб-сервер")
    print("  pyker-web --port 9000           # На другом порту")
    print("\n🚀 Запуск сервиса:")
    print("  sudo systemctl start pyker")
    print("  sudo systemctl status pyker")

if __name__ == "__main__":
    main() 