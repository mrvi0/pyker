#!/usr/bin/env python3
"""
Pyker CLI - командная строка для управления Python скриптами
"""

import argparse
import requests
import json
import sys
import os
import asyncio
from pathlib import Path
from typing import Optional
import signal
import time

# Импортируем ProcessManager для прямой работы
try:
    from src.process_manager import ProcessManager
    DIRECT_MODE = True
except ImportError:
    DIRECT_MODE = False

class PykerCLI:
    def __init__(self, base_url: str = "http://localhost:8000", direct_mode: bool = False):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.direct_mode = direct_mode
        
        if direct_mode and DIRECT_MODE:
            # Создаем локальный ProcessManager
            self.process_manager = ProcessManager()
            self._setup_signal_handlers()
        else:
            self.process_manager = None
    
    def _setup_signal_handlers(self):
        """Настраивает обработчики сигналов для graceful shutdown"""
        def signal_handler(signum, frame):
            print("\n🛑 Получен сигнал остановки, завершаем процессы...")
            if self.process_manager:
                # Останавливаем все процессы
                for process_id in list(self.process_manager.processes.keys()):
                    asyncio.create_task(self.process_manager.stop_process(process_id))
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """Выполняет HTTP запрос к API"""
        url = f"{self.api_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "DELETE":
                response = requests.delete(url)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            print(f"❌ Ошибка подключения к серверу {self.base_url}")
            print("Убедитесь, что Pyker сервер запущен: pyker start")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка API: {e}")
            sys.exit(1)
    
    async def start(self, name: str, script_path: str, auto_restart: bool = False):
        """Запускает процесс"""
        if not os.path.exists(script_path):
            print(f"❌ Файл не найден: {script_path}")
            sys.exit(1)
        
        if self.direct_mode:
            # Прямой режим - работаем с ProcessManager
            process_id = await self.process_manager.start_process(
                name=name,
                script_path=os.path.abspath(script_path),
                auto_restart=auto_restart
            )
            print(f"✅ Процесс '{name}' запущен (ID: {process_id})")
            
            # Запускаем event loop для управления процессами
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Остановка Pyker...")
                # Останавливаем все процессы
                for pid in list(self.process_manager.processes.keys()):
                    await self.process_manager.stop_process(pid)
        else:
            # API режим
            data = {
                "name": name,
                "script_path": os.path.abspath(script_path),
                "auto_restart": auto_restart
            }
            
            result = self._make_request("POST", "/processes", data)
            print(f"✅ Процесс '{name}' запущен (ID: {result['process_id']})")
    
    async def stop(self, process_id: str):
        """Останавливает процесс"""
        if self.direct_mode:
            success = await self.process_manager.stop_process(process_id)
            if success:
                print(f"✅ Процесс {process_id} остановлен")
            else:
                print(f"❌ Процесс {process_id} не найден")
        else:
            result = self._make_request("POST", f"/processes/{process_id}/stop")
            print(f"✅ Процесс остановлен")
    
    async def restart(self, process_id: str):
        """Перезапускает процесс"""
        if self.direct_mode:
            success = await self.process_manager.restart_process(process_id)
            if success:
                print(f"✅ Процесс {process_id} перезапущен")
            else:
                print(f"❌ Процесс {process_id} не найден")
        else:
            result = self._make_request("POST", f"/processes/{process_id}/restart")
            print(f"✅ Процесс перезапущен")
    
    async def delete(self, process_id: str):
        """Удаляет процесс"""
        if self.direct_mode:
            success = self.process_manager.delete_process(process_id)
            if success:
                print(f"✅ Процесс {process_id} удален")
            else:
                print(f"❌ Процесс {process_id} не найден")
        else:
            result = self._make_request("DELETE", f"/processes/{process_id}")
            print(f"✅ Процесс удален")
    
    def list(self):
        """Показывает список процессов"""
        if self.direct_mode:
            processes = self.process_manager.get_all_status()
        else:
            processes = self._make_request("GET", "/processes")
        
        if not processes:
            print("📋 Нет запущенных процессов")
            return
        
        print("📋 Список процессов:")
        print("-" * 80)
        print(f"{'ID':<20} {'Название':<20} {'Статус':<12} {'PID':<8} {'Автоперезапуск':<15}")
        print("-" * 80)
        
        for process in processes:
            pid = process.get('pid', '-')
            auto_restart = "✅" if process.get('auto_restart') else "❌"
            status_emoji = {
                'running': '🟢',
                'stopped': '🔴',
                'error': '🟡',
                'starting': '🟡'
            }.get(process['status'], '⚪')
            
            print(f"{process['id']:<20} {process['name']:<20} {status_emoji} {process['status']:<10} {pid:<8} {auto_restart:<15}")
    
    def logs(self, process_id: str, lines: int = 50):
        """Показывает логи процесса"""
        if self.direct_mode:
            logs = self.process_manager.get_process_logs(process_id, lines)
            if logs is None:
                print("❌ Процесс не найден")
                return
        else:
            logs_data = self._make_request("GET", f"/processes/{process_id}/logs?limit={lines}")
            logs = logs_data.get('logs', [])
        
        if not logs:
            print("📝 Логи отсутствуют")
            return
        
        print(f"📝 Логи процесса (последние {len(logs)} строк):")
        print("-" * 80)
        for log in logs:
            print(log)
    
    def status(self):
        """Показывает статус сервера"""
        if self.direct_mode:
            processes_count = len(self.process_manager.processes)
            active_processes = len([p for p in self.process_manager.processes.values() if p.status == "running"])
            print(f"🟢 Режим: Прямой (без сервера)")
            print(f"📊 Процессов: {processes_count}")
            print(f"🟢 Активных: {active_processes}")
        else:
            health = self._make_request("GET", "/health")
            print(f"🟢 Сервер: {health['status']}")
            print(f"📊 Процессов: {health['processes_count']}")
            print(f"🟢 Активных: {health['active_processes']}")
    
    def upload(self, script_path: str):
        """Загружает скрипт на сервер"""
        if self.direct_mode:
            print("ℹ️  В прямом режиме загрузка скриптов не требуется")
            print(f"📁 Используйте полный путь к скрипту: {os.path.abspath(script_path)}")
            return
        
        if not os.path.exists(script_path):
            print(f"❌ Файл не найден: {script_path}")
            sys.exit(1)
        
        if not script_path.endswith('.py'):
            print("❌ Файл должен быть Python скриптом (.py)")
            sys.exit(1)
        
        try:
            with open(script_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{self.api_url}/upload", files=files)
                response.raise_for_status()
                result = response.json()
                print(f"✅ Скрипт загружен: {result['filename']}")
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            sys.exit(1)

async def main():
    parser = argparse.ArgumentParser(
        description="Pyker - управление Python скриптами",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  pyker start mybot /path/to/script.py
  pyker start mybot script.py --auto-restart
  pyker list
  pyker logs process_id
  pyker stop process_id
  pyker restart process_id
  pyker delete process_id
  pyker upload script.py
  pyker status
  pyker start mybot script.py --direct  # Прямой режим без сервера
        """
    )
    
    parser.add_argument('--direct', action='store_true', 
                       help='Прямой режим (без веб-сервера)')
    parser.add_argument('--server', action='store_true',
                       help='Запустить веб-сервер')
    parser.add_argument('--api-url', default='http://localhost:8000',
                       help='URL API сервера (по умолчанию: http://localhost:8000)')
    
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Команда start
    start_parser = subparsers.add_parser('start', help='Запустить процесс')
    start_parser.add_argument('name', help='Название процесса')
    start_parser.add_argument('script', help='Путь к Python скрипту')
    start_parser.add_argument('--auto-restart', action='store_true', help='Автоматический перезапуск при ошибке')
    
    # Команда list
    subparsers.add_parser('list', help='Показать список процессов')
    
    # Команда logs
    logs_parser = subparsers.add_parser('logs', help='Показать логи процесса')
    logs_parser.add_argument('process_id', help='ID процесса')
    logs_parser.add_argument('-n', '--lines', type=int, default=50, help='Количество строк логов')
    
    # Команда stop
    stop_parser = subparsers.add_parser('stop', help='Остановить процесс')
    stop_parser.add_argument('process_id', help='ID процесса')
    
    # Команда restart
    restart_parser = subparsers.add_parser('restart', help='Перезапустить процесс')
    restart_parser.add_argument('process_id', help='ID процесса')
    
    # Команда delete
    delete_parser = subparsers.add_parser('delete', help='Удалить процесс')
    delete_parser.add_argument('process_id', help='ID процесса')
    
    # Команда upload
    upload_parser = subparsers.add_parser('upload', help='Загрузить скрипт')
    upload_parser.add_argument('script', help='Путь к Python скрипту')
    
    # Команда status
    subparsers.add_parser('status', help='Показать статус сервера')
    
    args = parser.parse_args()
    
    # Если указан флаг --server, запускаем веб-сервер
    if args.server:
        print("🌐 Запуск веб-сервера...")
        print("📱 Веб-интерфейс: http://localhost:8000")
        print("🔌 API документация: http://localhost:8000/docs")
        print("=" * 50)
        
        # Импортируем и запускаем сервер
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
        return
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Определяем режим работы
    # Прямой режим только для команды start или если явно указан --direct
    direct_mode = args.direct or (args.command == 'start')
    
    cli = PykerCLI(base_url=args.api_url, direct_mode=direct_mode)
    
    try:
        if args.command == 'start':
            asyncio.run(cli.start(args.name, args.script, args.auto_restart))
        elif args.command == 'list':
            cli.list()
        elif args.command == 'logs':
            cli.logs(args.process_id, args.lines)
        elif args.command == 'stop':
            asyncio.run(cli.stop(args.process_id))
        elif args.command == 'restart':
            asyncio.run(cli.restart(args.process_id))
        elif args.command == 'delete':
            asyncio.run(cli.delete(args.process_id))
        elif args.command == 'upload':
            cli.upload(args.script)
        elif args.command == 'status':
            cli.status()
    except KeyboardInterrupt:
        print("\n👋 Операция прервана")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 