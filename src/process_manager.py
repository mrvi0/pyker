import asyncio
import subprocess
import psutil
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ProcessInfo:
    id: str
    name: str
    script_path: str
    status: str  # running, stopped, error
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    logs: List[str] = None
    auto_restart: bool = False
    restart_count: int = 0
    max_restarts: int = 3

    def __post_init__(self):
        if self.logs is None:
            self.logs = []

class ProcessManager:
    def __init__(self):
        self.processes: Dict[str, ProcessInfo] = {}
        self.process_tasks: Dict[str, asyncio.Task] = {}
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
    def create_process_id(self, name: str) -> str:
        """Создает уникальный ID для процесса"""
        base_id = f"{name}_{int(time.time())}"
        counter = 1
        process_id = base_id
        
        while process_id in self.processes:
            process_id = f"{base_id}_{counter}"
            counter += 1
            
        return process_id

    async def start_process(self, name: str, script_path: str, auto_restart: bool = False) -> str:
        """Запускает Python скрипт"""
        process_id = self.create_process_id(name)
        
        process_info = ProcessInfo(
            id=process_id,
            name=name,
            script_path=script_path,
            status="starting",
            auto_restart=auto_restart
        )
        
        self.processes[process_id] = process_info
        
        # Запускаем процесс в отдельной задаче
        task = asyncio.create_task(self._run_process(process_id))
        self.process_tasks[process_id] = task
        
        logger.info(f"Запущен процесс {name} (ID: {process_id})")
        return process_id

    async def _run_process(self, process_id: str):
        """Внутренний метод для запуска процесса"""
        process_info = self.processes[process_id]
        
        while True:
            try:
                # Проверяем лимит перезапусков
                if process_info.restart_count >= process_info.max_restarts:
                    process_info.status = "error"
                    process_info.logs.append(f"[{datetime.now()}] Достигнут лимит перезапусков ({process_info.max_restarts})")
                    break
                
                process_info.status = "running"
                process_info.start_time = datetime.now()
                
                # Создаем процесс
                process = await asyncio.create_subprocess_exec(
                    "python", process_info.script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                process_info.pid = process.pid
                process_info.logs.append(f"[{datetime.now()}] Процесс запущен (PID: {process.pid})")
                
                # Читаем вывод процесса
                while True:
                    try:
                        line = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
                        if not line:
                            break
                        log_line = line.decode().strip()
                        process_info.logs.append(f"[{datetime.now()}] {log_line}")
                        
                        # Ограничиваем количество логов
                        if len(process_info.logs) > 1000:
                            process_info.logs = process_info.logs[-500:]
                            
                    except asyncio.TimeoutError:
                        # Проверяем, жив ли процесс
                        if process.returncode is not None:
                            break
                        continue
                
                # Ждем завершения процесса
                await process.wait()
                
                # Читаем stderr если есть
                stderr = await process.stderr.read()
                if stderr:
                    error_msg = stderr.decode().strip()
                    process_info.logs.append(f"[{datetime.now()}] ERROR: {error_msg}")
                
                process_info.logs.append(f"[{datetime.now()}] Процесс завершен с кодом {process.returncode}")
                
                # Если включен автоперезапуск и процесс завершился с ошибкой
                if process_info.auto_restart and process.returncode != 0:
                    process_info.restart_count += 1
                    process_info.logs.append(f"[{datetime.now()}] Перезапуск процесса (попытка {process_info.restart_count}/{process_info.max_restarts})")
                    await asyncio.sleep(5)  # Пауза перед перезапуском
                    continue
                else:
                    process_info.status = "stopped"
                    break
                    
            except Exception as e:
                process_info.status = "error"
                process_info.logs.append(f"[{datetime.now()}] Ошибка запуска: {str(e)}")
                logger.error(f"Ошибка в процессе {process_id}: {e}")
                break

    async def stop_process(self, process_id: str) -> bool:
        """Останавливает процесс"""
        if process_id not in self.processes:
            return False
            
        process_info = self.processes[process_id]
        
        if process_info.pid:
            try:
                # Завершаем процесс
                process = psutil.Process(process_info.pid)
                process.terminate()
                
                # Ждем завершения
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    process.kill()
                    
                process_info.status = "stopped"
                process_info.logs.append(f"[{datetime.now()}] Процесс остановлен")
                
            except psutil.NoSuchProcess:
                process_info.status = "stopped"
                process_info.logs.append(f"[{datetime.now()}] Процесс уже завершен")
        
        # Отменяем задачу
        if process_id in self.process_tasks:
            self.process_tasks[process_id].cancel()
            del self.process_tasks[process_id]
            
        return True

    async def restart_process(self, process_id: str) -> bool:
        """Перезапускает процесс"""
        if process_id not in self.processes:
            return False
            
        process_info = self.processes[process_id]
        
        # Останавливаем текущий процесс
        await self.stop_process(process_id)
        
        # Сбрасываем счетчик перезапусков
        process_info.restart_count = 0
        
        # Запускаем заново
        task = asyncio.create_task(self._run_process(process_id))
        self.process_tasks[process_id] = task
        
        return True

    def get_process_status(self, process_id: str) -> Optional[ProcessInfo]:
        """Получает статус процесса"""
        return self.processes.get(process_id)

    def get_all_status(self) -> List[Dict]:
        """Получает статус всех процессов"""
        return [asdict(process_info) for process_info in self.processes.values()]

    def get_process_logs(self, process_id: str, limit: int = 100) -> List[str]:
        """Получает логи процесса"""
        if process_id not in self.processes:
            return []
            
        process_info = self.processes[process_id]
        return process_info.logs[-limit:]

    def delete_process(self, process_id: str) -> bool:
        """Удаляет процесс из списка"""
        if process_id not in self.processes:
            return False
            
        # Останавливаем процесс если запущен
        asyncio.create_task(self.stop_process(process_id))
        
        # Удаляем из словарей
        del self.processes[process_id]
        if process_id in self.process_tasks:
            del self.process_tasks[process_id]
            
        return True 