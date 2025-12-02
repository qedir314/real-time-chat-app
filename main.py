import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from auth.core import get_user_from_token
from routes import auth, chat
from routes.chat import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis
    print("🚀 Starting up...")
    await manager.initialize_redis()
    yield
    # Shutdown: Cleanup Redis
    print("🛑 Shutting down...")
    await manager.shutdown()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
async def read_root(request: Request):
    token = request.cookies.get("access_token")
    if token:
        user = await get_user_from_token(token.split(" ")[1])
        if user:
            return templates.TemplateResponse("index.html", {"request": request, "user": user, "token": token.split(" ")[1]})
    return RedirectResponse(url="/signin")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
