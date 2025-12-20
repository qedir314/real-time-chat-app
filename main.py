import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from anyio import to_thread

from routes import auth, chat, rooms
from routes.chat import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # System Tuning: Increase thread pool for blocking tasks (Bcrypt/Mongo)
    limiter = to_thread.current_default_thread_limiter()
    limiter.total_tokens = 100
    
    # Startup: Initialize Redis
    print("🚀 Starting up...")
    await manager.initialize_redis()
    yield
    # Shutdown: Cleanup Redis
    print("🛑 Shutting down...")
    await manager.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(rooms.router)

@app.get("/")
async def read_root():
    return {"status": "API is running", "frontend": "http://localhost:5173"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
