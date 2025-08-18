#!/usr/bin/env python3
"""
Скрипт удаления Pyker
"""

import os
import sys
import subprocess
import shutil

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

def stop_service():
    """Останавливает и отключает сервис"""
    print("🛑 Остановка сервиса...")
    
    # Останавливаем сервис
    run_command("systemctl stop pyker.service")
    
    # Отключаем автозапуск
    run_command("systemctl disable pyker.service")
    
    # Удаляем файл сервиса
    if os.path.exists("/etc/systemd/system/pyker.service"):
        os.remove("/etc/systemd/system/pyker.service")
        print("  ✅ Файл сервиса удален")
    
    # Перезагружаем systemd
    run_command("systemctl daemon-reload")

def remove_files():
    """Удаляет файлы Pyker"""
    print("🗑️  Удаление файлов...")
    
    # Удаляем CLI команды
    if os.path.exists("/usr/local/bin/pyker"):
        os.remove("/usr/local/bin/pyker")
        print("  ✅ CLI команда pyker удалена")
    
    if os.path.exists("/usr/local/bin/pyker-web"):
        os.remove("/usr/local/bin/pyker-web")
        print("  ✅ CLI команда pyker-web удалена")
    
    # Удаляем директорию Pyker
    if os.path.exists("/opt/pyker"):
        shutil.rmtree("/opt/pyker")
        print("  ✅ Директория /opt/pyker удалена")
    
    # Удаляем логи
    if os.path.exists("/var/log/pyker"):
        shutil.rmtree("/var/log/pyker")
        print("  ✅ Логи удалены")

def main():
    print("🗑️  Удаление Pyker - Python Script Manager")
    print("=" * 50)
    
    # Проверяем права root
    check_root()
    
    # Подтверждение удаления
    response = input("Вы уверены, что хотите удалить Pyker? (y/N): ")
    if response.lower() != 'y':
        print("❌ Удаление отменено")
        sys.exit(0)
    
    # Останавливаем сервис
    stop_service()
    
    # Удаляем файлы
    remove_files()
    
    print("\n✅ Pyker успешно удален!")

if __name__ == "__main__":
    main() 