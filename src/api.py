from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import aiofiles
from pathlib import Path
import json

from .process_manager import ProcessManager

router = APIRouter()

# Глобальный экземпляр менеджера процессов будет установлен из main.py
process_manager = None

def set_process_manager(manager: ProcessManager):
    global process_manager
    process_manager = manager

# Pydantic модели
class ProcessStartRequest(BaseModel):
    name: str
    script_path: str
    auto_restart: bool = False

class ProcessResponse(BaseModel):
    id: str
    name: str
    script_path: str
    status: str
    pid: Optional[int] = None
    start_time: Optional[str] = None
    auto_restart: bool = False
    restart_count: int = 0

@router.get("/processes", response_model=List[ProcessResponse])
async def get_processes():
    """Получить список всех процессов"""
    if process_manager is None:
        raise HTTPException(status_code=500, detail="Process manager not initialized")
    processes = process_manager.get_all_status()
    return processes

@router.get("/processes/{process_id}")
async def get_process(process_id: str):
    """Получить информацию о конкретном процессе"""
    if process_manager is None:
        raise HTTPException(status_code=500, detail="Process manager not initialized")
    process = process_manager.get_process_status(process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Процесс не найден")
    return process

@router.post("/processes")
async def start_process(request: ProcessStartRequest):
    """Запустить новый процесс"""
    if process_manager is None:
        raise HTTPException(status_code=500, detail="Process manager not initialized")
    
    try:
        # Проверяем существование файла
        script_path = Path(request.script_path)
        if not script_path.exists():
            raise HTTPException(status_code=400, detail="Файл скрипта не найден")
        
        process_id = await process_manager.start_process(
            name=request.name,
            script_path=str(script_path),
            auto_restart=request.auto_restart
        )
        
        return {"process_id": process_id, "message": "Процесс запущен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска процесса: {str(e)}")

@router.post("/processes/{process_id}/stop")
async def stop_process(process_id: str):
    """Остановить процесс"""
    if process_manager is None:
        raise HTTPException(status_code=500, detail="Process manager not initialized")
    success = await process_manager.stop_process(process_id)
    if not success:
        raise HTTPException(status_code=404, detail="Процесс не найден")
    return {"message": "Процесс остановлен"}

@router.post("/processes/{process_id}/restart")
async def restart_process(process_id: str):
    """Перезапустить процесс"""
    if process_manager is None:
        raise HTTPException(status_code=500, detail="Process manager not initialized")
    success = await process_manager.restart_process(process_id)
    if not success:
        raise HTTPException(status_code=404, detail="Процесс не найден")
    return {"message": "Процесс перезапущен"}

@router.delete("/processes/{process_id}")
async def delete_process(process_id: str):
    """Удалить процесс"""
    if process_manager is None:
        raise HTTPException(status_code=500, detail="Process manager not initialized")
    success = process_manager.delete_process(process_id)
    if not success:
        raise HTTPException(status_code=404, detail="Процесс не найден")
    return {"message": "Процесс удален"}

@router.get("/processes/{process_id}/logs")
async def get_process_logs(process_id: str, limit: int = 100):
    """Получить логи процесса"""
    if process_manager is None:
        raise HTTPException(status_code=500, detail="Process manager not initialized")
    logs = process_manager.get_process_logs(process_id, limit)
    if logs is None:
        raise HTTPException(status_code=404, detail="Процесс не найден")
    return {"logs": logs}

@router.post("/upload")
async def upload_script(file: UploadFile = File(...)):
    """Загрузить Python скрипт"""
    if not file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Файл должен быть Python скриптом (.py)")
    
    # Создаем папку scripts если не существует
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    # Сохраняем файл
    file_path = scripts_dir / file.filename
    
    try:
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return {
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {str(e)}")

@router.get("/scripts")
async def list_scripts():
    """Получить список доступных скриптов"""
    scripts_dir = Path("scripts")
    if not scripts_dir.exists():
        return {"scripts": []}
    
    scripts = []
    for script_file in scripts_dir.glob("*.py"):
        scripts.append({
            "name": script_file.name,
            "path": str(script_file),
            "size": script_file.stat().st_size
        })
    
    return {"scripts": scripts}

@router.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    if process_manager is None:
        return {
            "status": "error",
            "processes_count": 0,
            "active_processes": 0
        }
    return {
        "status": "healthy",
        "processes_count": len(process_manager.processes),
        "active_processes": len([p for p in process_manager.processes.values() if p.status == "running"])
    } 