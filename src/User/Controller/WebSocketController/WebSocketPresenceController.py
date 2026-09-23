from fastapi import WebSocket
from typing import Dict

class WebSocketPresenceController:
    def __init__(self):
        # 🪐 Active mapping registry: Tracks dict of {user_id: WebSocket_Instance}
        self.active_connections: Dict[int, WebSocket] = {}

    async def register_connection(self, user_id: int, websocket: WebSocket):
        """Accepts the incoming websocket connection and broadcasts the user's online state."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # 📢 Push real-time event to all connected network clients
        await self.broadcast_status_event(user_id, status="online")

    def remove_connection(self, user_id: int):
        """Removes the disconnected socket channel cleanly from the tracking registry."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def broadcast_status_event(self, user_id: int, status: str):
        """Loops through every active client array channel and pushes the updated JSON frame."""
        payload = {
            "type": "STATUS_UPDATE",
            "userId": user_id,
            # 💡 Keeps  legacy boolean frontend trackers happy (True if status is "online")
            "isOnline": status == "online", 
            # 💡 Supplies the modern multi-state string tracker to your UI
            "status": status
        }
        
        for client_id, connection in list(self.active_connections.items()):
            try:
                # 📡 Direct network broadcast stream push
                await connection.send_json(payload)
            except Exception:
                # Stale client channel catch: remove connection array automatically if dead
                self.remove_connection(client_id)

# 💡 Instantiate a single shared tracking controller to import across your application routes
presence_controller = WebSocketPresenceController()
