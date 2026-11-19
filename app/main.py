from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.database import create_database_tables, engine
from app.routes.sessions import router as sessions_router
from app.routes.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_database_tables()
    yield
    await engine.dispose()

def create_app():
    cfg = get_settings()
    application = FastAPI(title="Full-Stack AI Chat Application", version="1.0.0", lifespan=lifespan)
    application.add_middleware(CORSMiddleware, allow_origins=cfg.cors_origins,
                               allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
    application.include_router(sessions_router)
    application.include_router(chat_router)
    frontend = Path(__file__).resolve().parent.parent / "frontend"
    if frontend.exists():
        application.mount("/static", StaticFiles(directory=frontend), name="static")
        @application.get("/", include_in_schema=False)
        async def index():
            return FileResponse(frontend / "index.html")
    @application.get("/health", tags=["health"])
    async def health():
        return {"status": "ok"}
    return application

app = create_app()
