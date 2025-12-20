from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from models.room import Room, RoomCreate, RoomJoin
from config.database import rooms_collection, users_collection
from auth.core import get_current_active_user, get_password_hash, verify_password
import uuid
from datetime import datetime, UTC

router = APIRouter(tags=["rooms"])

@router.post("/rooms/create", response_model=Room)
async def create_room(room_in: RoomCreate, current_user: dict = Depends(get_current_active_user)):
    room_data = {
        "name": room_in.name,
        "owner_id": current_user["_id"],
        "members": [current_user["_id"]],
        "room_id": str(uuid.uuid4()),
        "invite_code": str(uuid.uuid4())[:8],
        "created_at": datetime.now(UTC)
    }
    
    if room_in.password:
        room_data["hashed_password"] = get_password_hash(room_in.password)
        
    new_room = Room(**room_data)
    rooms_collection.insert_one(new_room.model_dump())
    return new_room

@router.get("/rooms/mine", response_model=List[Room])
async def get_my_rooms(current_user: dict = Depends(get_current_active_user)):
    user_id = current_user["_id"]
    cursor = rooms_collection.find({"members": user_id})
    rooms = []
    for doc in cursor:
        rooms.append(Room(**doc))
    return rooms

@router.post("/rooms/join", response_model=Room)
async def join_room(join_data: RoomJoin, current_user: dict = Depends(get_current_active_user)):
    user_id = current_user["_id"]
    room = None
    
    if join_data.invite_code:
        room = rooms_collection.find_one({"invite_code": join_data.invite_code})
        if not room:
            raise HTTPException(status_code=404, detail="Invalid invite code")
            
    elif join_data.room_id:
        room = rooms_collection.find_one({"room_id": join_data.room_id})
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
            
        if room.get("hashed_password"):
            if not join_data.password:
                raise HTTPException(status_code=400, detail="Password required for this room")
            if not verify_password(join_data.password, room["hashed_password"]):
                 raise HTTPException(status_code=403, detail="Invalid password")
    else:
        raise HTTPException(status_code=400, detail="Must provide invite_code or room_id")

    if user_id not in room["members"]:
        rooms_collection.update_one(
            {"room_id": room["room_id"]},
            {"$push": {"members": user_id}}
        )
        room["members"].append(user_id)
        
    return Room(**room)

@router.post("/rooms/{room_id}/refresh_invite", response_model=Room)
async def refresh_invite_code(room_id: str, current_user: dict = Depends(get_current_active_user)):
    room = rooms_collection.find_one({"room_id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    if room["owner_id"] != current_user["_id"]:
         raise HTTPException(status_code=403, detail="Only owner can refresh invite code")
         
    new_code = str(uuid.uuid4())[:8]
    rooms_collection.update_one(
        {"room_id": room_id},
        {"$set": {"invite_code": new_code}}
    )
    room["invite_code"] = new_code
    return Room(**room)
