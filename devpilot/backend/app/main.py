from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import files, health, projects, repo_intel
from app.api import import_routes
from app.config import settings
from app.db.database import Base, engine

# Phase 1: create tables directly from the models on startup. A real
# migration tool (Alembic) should replace this before this app has
# production data worth preserving — see docs/architecture.md.
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(files.router)
app.include_router(repo_intel.router)
app.include_router(import_routes.router)
