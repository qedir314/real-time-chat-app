from fastapi import APIRouter, Depends, HTTPException
from config.database import users_collection, messages_collection
from auth.core import get_current_active_user
from typing import List
from datetime import datetime
import os

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users")
async def get_all_users_stats(current_user: dict = Depends(get_current_active_user)):
    # Check if current_user is the super user
    admin_username = os.getenv("ADMIN_USERNAME")
    if not admin_username or current_user.get("username") != admin_username:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users_cursor = users_collection.find({})
    users_stats = []
    
    for user in users_cursor:
        username = user.get("username")
        message_count = messages_collection.count_documents({"user": username})
        
        last_active = user.get("last_active")
        if isinstance(last_active, datetime):
            last_active = last_active.isoformat()
            
        users_stats.append({
            "username": username,
            "is_active": user.get("is_active", False),
            "last_active": last_active,
            "total_messages": message_count
        })
        
    return users_stats
