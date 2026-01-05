import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse as FastAPIFileResponse
from starlette.concurrency import run_in_threadpool

from auth.core import get_current_active_user
from config.database import files_collection, rooms_collection
from models.file import FileMetadata, FileResponse
from datetime import datetime, UTC

router = APIRouter(prefix="/files", tags=["files"])

# Configuration
UPLOAD_DIR = Path("/app/uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    # Documents
    ".pdf", ".doc", ".docx", ".txt",
    # Archives
    ".zip"
}
ALLOWED_CONTENT_TYPES = {
    # Images
    "image/jpeg", "image/png", "image/gif", "image/webp",
    # Documents
    "application/pdf", 
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    # Archives
    "application/zip", "application/x-zip-compressed"
}


def ensure_upload_dir():
    """Create upload directory if it doesn't exist"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def validate_file(file: UploadFile) -> None:
    """Validate file type and size"""
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Content type '{file.content_type}' not allowed"
        )


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    room_id: str = Form(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Upload a file to a chat room"""
    
    # Validate user is member of room
    def check_membership():
        return rooms_collection.find_one({"room_id": room_id})
    
    room = await run_in_threadpool(check_membership)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if current_user["_id"] not in room.get("members", []):
        raise HTTPException(status_code=403, detail="Not a member of this room")
    
    # Validate file
    validate_file(file)
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    ext = Path(file.filename).suffix.lower()
    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / stored_name
    
    # Ensure upload directory exists
    ensure_upload_dir()
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Create metadata
    file_metadata = FileMetadata(
        original_name=file.filename,
        stored_name=stored_name,
        content_type=file.content_type,
        size=len(content),
        uploader=current_user["username"],
        room_id=room_id
    )
    
    # Save metadata to database
    await run_in_threadpool(
        lambda: files_collection.insert_one(file_metadata.model_dump())
    )
    
    return FileResponse(
        file_id=file_metadata.file_id,
        original_name=file_metadata.original_name,
        content_type=file_metadata.content_type,
        size=file_metadata.size,
        url=f"/api/files/{file_metadata.file_id}"
    )


@router.get("/{file_id}")
async def download_file(
    file_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Download or view a file"""
    
    # Get file metadata
    def get_file():
        return files_collection.find_one({"file_id": file_id})
    
    file_meta = await run_in_threadpool(get_file)
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check user has access to the room
    def check_room():
        return rooms_collection.find_one({"room_id": file_meta["room_id"]})
    
    room = await run_in_threadpool(check_room)
    if room and current_user["_id"] not in room.get("members", []):
        raise HTTPException(status_code=403, detail="Not authorized to access this file")
    
    # Get file path
    file_path = UPLOAD_DIR / file_meta["stored_name"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Determine if file should be displayed inline or downloaded
    content_type = file_meta["content_type"]
    is_inline = content_type.startswith("image/") or content_type == "application/pdf"
    
    return FastAPIFileResponse(
        path=str(file_path),
        filename=file_meta["original_name"],
        media_type=content_type,
        content_disposition_type="inline" if is_inline else "attachment"
    )


@router.get("/{file_id}/info")
async def get_file_info(
    file_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get file metadata"""
    
    def get_file():
        return files_collection.find_one({"file_id": file_id})
    
    file_meta = await run_in_threadpool(get_file)
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check user has access to the room
    def check_room():
        return rooms_collection.find_one({"room_id": file_meta["room_id"]})
    
    room = await run_in_threadpool(check_room)
    if room and current_user["_id"] not in room.get("members", []):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "file_id": file_meta["file_id"],
        "original_name": file_meta["original_name"],
        "content_type": file_meta["content_type"],
        "size": file_meta["size"],
        "uploader": file_meta["uploader"],
        "uploaded_at": file_meta["uploaded_at"].isoformat() if isinstance(file_meta["uploaded_at"], datetime) else file_meta["uploaded_at"],
        "url": f"/api/files/{file_meta['file_id']}"
    }
