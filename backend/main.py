from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from routes.chat import router as chat_router
from routes.health import router as health_router
from utils.config import settings
from utils.logging import configure_logging


configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} is running"}


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """Return all HTTP errors in a consistent JSON shape."""
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(status_code=exc.status_code, content={"error": message})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return validation errors in a consistent JSON shape."""
    for error in exc.errors():
        location = error.get("loc", [])
        if "sessionId" in location:
            return JSONResponse(
                status_code=400,
                content={"error": "sessionId is required."},
            )
        if "message" in location:
            return JSONResponse(
                status_code=400,
                content={"error": "message is required."},
            )

    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request payload."},
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.app_host, port=10000, reload=False)