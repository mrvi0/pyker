import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import logging
from pathlib import Path

from src.process_manager import ProcessManager
from src.api import router as api_router, set_process_manager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Pyker - Python Script Manager",
    description="Современный инструмент для управления Python скриптами",
    version="1.0.0"
)

# Менеджер процессов
process_manager = ProcessManager()

# Устанавливаем менеджер в API
set_process_manager(process_manager)

# Подключение API роутера
app.include_router(api_router, prefix="/api")

# WebSocket соединения
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Удаляем неактивные соединения
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "get_status":
                status = process_manager.get_all_status()
                await manager.send_personal_message(
                    json.dumps({"type": "status", "data": status}), 
                    websocket
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Подключение статических файлов (React приложение)
if Path("frontend/build").exists():
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
    
    @app.get("/")
    async def read_index():
        return FileResponse("frontend/build/index.html")
    
    @app.get("/{full_path:path}")
    async def read_other(full_path: str):
        return FileResponse("frontend/build/index.html")

# Запуск приложения
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 