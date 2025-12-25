import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from anyio import to_thread

from routes import auth, chat, rooms, admin
from routes.chat import manager
from auth.core import get_password_hash
from config.database import users_collection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # System Tuning: Increase thread pool for blocking tasks (Bcrypt/Mongo)
    limiter = to_thread.current_default_thread_limiter()
    limiter.total_tokens = 100
    
    # Startup: Initialize Redis
    print("🚀 Starting up...")
    await manager.initialize_redis()

    # Create Super User if configured
    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    if admin_user and admin_pass:
        await to_thread.run_sync(
            lambda: users_collection.update_one(
                {"username": admin_user},
                {
                    "$setOnInsert": {
                        "username": admin_user,
                        "hashed_password": get_password_hash(admin_pass),
                        "is_active": False,
                        "created_at": datetime.now()
                    }
                },
                upsert=True
            )
        )
        print(f"👤 Admin user '{admin_user}' ensured.")

    yield
    # Shutdown: Cleanup Redis
    print("🛑 Shutting down...")
    await manager.shutdown()

app = FastAPI(lifespan=lifespan)

# Get CORS origins from environment variable
origins_env = os.getenv("CORS_ORIGINS", "*")
origins = origins_env.split(",") if origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(rooms.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/")
async def read_root():
    return {"status": "API is running"}


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=8000, reload=True)
