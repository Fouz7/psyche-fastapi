from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.session import create_all
from app.controllers.auth_controller import router as auth_router
from app.controllers.mental_controller import router as mental_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_all()
    yield

app = FastAPI(title="Psyche API", lifespan=lifespan)


# Health/root endpoints
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


# Routers
app.include_router(auth_router)
app.include_router(mental_router)
