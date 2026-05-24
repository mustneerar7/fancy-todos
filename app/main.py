from fastapi import FastAPI

from app.internal import admin
from app.routers import items, users

app = FastAPI()

app.include_router(users.router)
app.include_router(items.router)
app.include_router(admin.router, prefix="/admin", tags=["admin"])
