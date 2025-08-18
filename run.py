#!/usr/bin/env python3
"""
Скрипт для запуска Pyker
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    try:
        import fastapi
        import uvicorn
        print("✅ Python зависимости установлены")
    except ImportError:
        print("❌ Python зависимости не установлены")
        print("Установите зависимости: pip install -r requirements.txt")
        return False
    return True

def build_frontend():
    """Собирает фронтенд"""
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Папка frontend не найдена")
        return False
    
    print("🔨 Сборка фронтенда...")
    try:
        # Проверяем наличие node_modules
        if not (frontend_dir / "node_modules").exists():
            print("📦 Установка npm зависимостей...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        
        # Собираем проект
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
        print("✅ Фронтенд собран")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка сборки фронтенда: {e}")
        return False
    except FileNotFoundError:
        print("❌ Node.js/npm не установлен")
        return False

def main():
    print("🚀 Запуск Pyker - Python Script Manager")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_dependencies():
        sys.exit(1)
    
    # Собираем фронтенд
    if not build_frontend():
        print("⚠️  Фронтенд не собран, запускаем только backend")
    
    print("🌐 Запуск сервера...")
    print("📱 Веб-интерфейс будет доступен по адресу: http://localhost:8000")
    print("🔌 API документация: http://localhost:8000/docs")
    print("=" * 50)
    
    # Запускаем сервер
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")

if __name__ == "__main__":
    main() 