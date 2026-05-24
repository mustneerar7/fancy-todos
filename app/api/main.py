from fastapi import APIRouter

from app.api.routes import login, todos, users, utils

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(todos.router)
api_router.include_router(utils.router)
