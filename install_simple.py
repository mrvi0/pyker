#!/usr/bin/env python3
"""
Простой скрипт установки Pyker
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_root():
    """Проверяет права root"""
    if os.geteuid() != 0:
        print("❌ Этот скрипт должен быть запущен с правами root (sudo)")
        sys.exit(1)

def install_dependencies():
    """Устанавливает зависимости"""
    print("📦 Установка зависимостей...")
    
    # Обновляем пакеты
    run_command("apt update")
    
    # Устанавливаем Python и pip
    deps = ["python3", "python3-pip"]
    
    for dep in deps:
        print(f"  Устанавливаем {dep}...")
        success, _, error = run_command(f"apt install -y {dep}")
        if not success:
            print(f"❌ Ошибка установки {dep}: {error}")
            return False
    
    # Устанавливаем psutil
    print("  Устанавливаем psutil...")
    success, _, error = run_command("pip3 install psutil")
    if not success:
        print(f"❌ Ошибка установки psutil: {error}")
        return False
    
    return True

def install_pyker():
    """Устанавливает Pyker"""
    print("🔧 Установка Pyker...")
    
    # Создаем директории
    pyker_dir = Path("/usr/local/bin")
    pyker_dir.mkdir(exist_ok=True)
    
    # Копируем файл
    if os.path.exists("pyker.py"):
        shutil.copy2("pyker.py", "/usr/local/bin/pyker")
        os.chmod("/usr/local/bin/pyker", 0o755)
        print("  ✅ Pyker установлен в /usr/local/bin/pyker")
    else:
        print("  ❌ Файл pyker.py не найден")
        return False
    
    return True

def main():
    print("🚀 Установка Pyker - простая утилита для Python скриптов")
    print("=" * 60)
    
    # Проверяем права root
    check_root()
    
    # Устанавливаем зависимости
    if not install_dependencies():
        print("❌ Ошибка установки зависимостей")
        sys.exit(1)
    
    # Устанавливаем Pyker
    if not install_pyker():
        print("❌ Ошибка установки Pyker")
        sys.exit(1)
    
    print("\n🎉 Установка завершена!")
    print("=" * 60)
    print("📋 Команды:")
    print("  pyker start <name> <script>     # Запустить скрипт")
    print("  pyker list                      # Список процессов")
    print("  pyker logs <name>               # Показать логи")
    print("  pyker stop <name>               # Остановить процесс")
    print("  pyker restart <name>            # Перезапустить")
    print("  pyker delete <name>             # Удалить процесс")
    print("  pyker status                    # Общий статус")
    print("\n📝 Примеры:")
    print("  pyker start mybot /path/to/bot.py")
    print("  pyker list")
    print("  pyker logs mybot -f")

if __name__ == "__main__":
    main() 