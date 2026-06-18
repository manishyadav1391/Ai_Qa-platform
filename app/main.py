# FastAPI app entry point
from fastapi import FastAPI
from app.database.db import engine
from app.database.db import Base
from app.database import models
from app.routes.project_routes import router as project_router
from app.routes.crawl_routes import router as crawl_router
from app.routes.testcase_routes import (
    router as testcase_router
)
from app.routes.ai_routes import router as ai_router
from app.routes.script_routes import (
    router as script_router
)
from app.routes.execution_routes import router as execution_router
from app.routes.page_routes import router as page_router
from fastapi.middleware.cors import CORSMiddleware



Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI QA Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(project_router)
app.include_router(crawl_router)

app.include_router(
    testcase_router
)
app.include_router(ai_router)
app.include_router(
    script_router
)
app.include_router(execution_router)
app.include_router(page_router)

@app.get("/")
def home():
    return {
        "message": "AI QA Platform Running"
    }


@app.post("/crawl")
def crawl():
    return {
        "status": "started"
    }