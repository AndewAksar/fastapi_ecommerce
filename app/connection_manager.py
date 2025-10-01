from fastapi import WebSocket
from typing import List


# Определение класса для управления соединениями клиентов
class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    # Метод для добавления нового соединения клиента
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    # Метод для удаления соединения клиента
    async def broadcast(self, data: str):
        for connection in self.connections:
            await connection.send_text(data)