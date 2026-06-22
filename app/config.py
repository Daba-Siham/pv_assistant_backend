from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "PV Intelligent Assistant API"
    PROJECT_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development")

    DEBUG: bool = Field(default=True)

    FRONTEND_URL: str = Field(default="http://localhost:5173")
    BACKEND_URL: str = Field(default="http://localhost:8000")

    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000"
        ]
    )

    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/pv_assistant"
    )

    SECRET_KEY: str = Field(default="change-this-secret-key")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    LLM_PROVIDER: str = Field(default="ollama")
    LLM_MODEL: str = Field(default="llama3")
    LLM_TEMPERATURE: float = Field(default=0.2)
    LLM_MAX_TOKENS: int = Field(default=1000)

    OPENAI_API_KEY: str | None = Field(default=None)
    GROQ_API_KEY: str | None = Field(default=None)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")

    NSRDB_API_KEY: str | None = Field(default=None)
    NSRDB_BASE_URL: str = Field(default="https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv")

    PANELS_DATA_PATH: Path = Field(default=DATA_DIR / "materials" / "panels.csv")
    BATTERIES_DATA_PATH: Path = Field(default=DATA_DIR / "materials" / "batteries.csv")
    INVERTERS_DATA_PATH: Path = Field(default=DATA_DIR / "materials" / "inverters.csv")
    PRICES_DATA_PATH: Path = Field(default=DATA_DIR / "materials" / "prices.csv")
    STORES_DATA_PATH: Path = Field(default=DATA_DIR / "stores" / "stores.csv")
    SOLAR_DATA_DIR: Path = Field(default=DATA_DIR / "solar")
    SIMULATION_DATA_PATH: Path = Field(default=DATA_DIR / "simulations" / "monitoring_samples.csv")
    RAG_DOCS_DIR: Path = Field(default=DATA_DIR / "rag_docs")

    VECTOR_STORE_DIR: Path = Field(default=BASE_DIR / "vector_store")
    PV_RECOMMENDATION_MODEL_PATH: Path = Field(
        default=BASE_DIR / "app" / "ml_models" / "pv_recommendation_model_bundle_v2.joblib"
    )

    DEFAULT_PERFORMANCE_RATIO: float = Field(default=0.75)
    DEFAULT_BATTERY_DOD: float = Field(default=0.8)
    DEFAULT_BATTERY_EFFICIENCY: float = Field(default=0.9)
    DEFAULT_INVERTER_MARGIN: float = Field(default=1.25)
    DEFAULT_ELECTRICITY_PRICE: float = Field(default=1.5)

    DEFAULT_SYSTEM_LOSSES: float = Field(default=0.14)
    DEFAULT_SHADE_FACTOR: float = Field(default=1.0)

    EXPOSE_RAW_ML_RESPONSE: bool = Field(default=False)

    LOG_LEVEL: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
