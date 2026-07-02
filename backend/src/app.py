from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.v1 import auth, customers, og, payments, plans
from src.core.config import get_settings


async def env_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Any]],
) -> Any:
    env: dict[str, Any] = request.scope.get("env", {})
    get_settings(env)
    return await call_next(request)


app = FastAPI(title="Lipa Polepole API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(env_middleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(og.router)


@app.get("/")
def root():
    return {"message": "Lipa Polepole API is running"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )
