from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "RAG GenAI Assistant")
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    cors_origins: list[str] = None

    def __post_init__(self) -> None:
        origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        object.__setattr__(
            self,
            "cors_origins",
            [origin.strip() for origin in origins.split(",") if origin.strip()],
        )


settings = Settings()
