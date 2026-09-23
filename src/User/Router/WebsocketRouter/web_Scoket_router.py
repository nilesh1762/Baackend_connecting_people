from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect,status
from requests import Session
from src.User.Controller.WebSocketController.WebSocketPresenceController import presence_controller
from sqlalchemy import update
from src.User.model import Friendship, UserModel
from src.utils.db import init_db , Session  
import json

ws_router  = APIRouter(prefix="/user", tags=["Real-time System Presence Paths"], redirect_slashes=True)

@ws_router.websocket("/{user_id}")
async def websocket_presence_endpoint(websocket: WebSocket, user_id: int):
    # 1. Mount connection tracking array
    await presence_controller.register_connection(user_id, websocket)
    
    # 🟢 CRITICAL FIXED LINE: Instantiate an isolated database session manually
    db = Session()
    
    try:
        # 🟢 Force state to "online" inside database on initial connection handshake
        db.execute(update(UserModel).where(UserModel.id == user_id).values(status_presence="online"))
        db.commit()
        
        # 🟢 Immediately broadcast to the network so friends' tabs turn green in real-time
        await presence_controller.broadcast_status_event(user_id, status="online")
            
        while True:
            # 2. ⚡ CHAT FORWARDING: Listen for manual status shifts from the React app
            client_message = await websocket.receive_text()
            data = json.loads(client_message)
           

            if data.get("type") == "CHANGE_STATUS":
                new_status = data.get("status") # "away", "online", or "offline"
             
                db.execute(update(UserModel).where(UserModel.id == user_id).values(status_presence=new_status))
                db.commit()
                
                # Broadcast the manual status change out to all active friends
                await presence_controller.broadcast_status_event(user_id, status=new_status)
            
    except WebSocketDisconnect:
        presence_controller.remove_connection(user_id)
        
        # 3. Force state back to "offline" on browser window termination
        db.execute(update(UserModel).where(UserModel.id == user_id).values(status_presence="offline"))
        db.commit()
        await presence_controller.broadcast_status_event(user_id, status="offline")
        
    finally:
        # 🟢 Cleanly release the standalone session back into your Oracle database connection pool
        db.close()