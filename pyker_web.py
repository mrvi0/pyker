#!/usr/bin/env python3
"""
Pyker Web Server - веб-интерфейс для Pyker
"""

import uvicorn
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Pyker Web Server - веб-интерфейс для управления Python скриптами",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  pyker-web                    # Запуск на localhost:8000
  pyker-web --host 0.0.0.0     # Запуск на всех интерфейсах
  pyker-web --port 9000        # Запуск на порту 9000
  pyker-web --reload           # Режим разработки с автоперезагрузкой
        """
    )
    
    parser.add_argument('--host', default='0.0.0.0', 
                       help='Хост для запуска сервера (по умолчанию: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Порт для запуска сервера (по умолчанию: 8000)')
    parser.add_argument('--reload', action='store_true',
                       help='Режим разработки с автоперезагрузкой')
    parser.add_argument('--workers', type=int, default=1,
                       help='Количество воркеров (по умолчанию: 1)')
    
    args = parser.parse_args()
    
    print("🌐 Pyker Web Server")
    print("=" * 50)
    print(f"📱 Веб-интерфейс: http://{args.host}:{args.port}")
    print(f"🔌 API документация: http://{args.host}:{args.port}/docs")
    print(f"📖 ReDoc: http://{args.host}:{args.port}/redoc")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1
        )
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 