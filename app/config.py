import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    mongodb_uri: str
    mongodb_db_name: str = "mcq_generator"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    cors_origins: list[str]
    quality_encoder_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    quality_cola_model: str = "textattack/distilbert-base-uncased-CoLA"
    nlp_inference_workers: int = 1
    preload_nlp_models: bool = True

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self.gemini_api_key = api_key
        self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)

        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError(
                "MONGODB_URI is not set. Copy .env.example to .env and add your connection string."
            )
        self.mongodb_uri = mongodb_uri
        self.mongodb_db_name = os.getenv("MONGODB_DB_NAME", self.mongodb_db_name)

        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            raise ValueError(
                "JWT_SECRET_KEY is not set. Copy .env.example to .env and add a secret key."
            )
        self.jwt_secret_key = jwt_secret
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", self.jwt_algorithm)
        self.jwt_expire_minutes = int(
            os.getenv("JWT_EXPIRE_MINUTES", str(self.jwt_expire_minutes))
        )

        raw_origins = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
        self.cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

        self.quality_encoder_model = os.getenv(
            "QUALITY_ENCODER_MODEL", self.quality_encoder_model
        )
        self.quality_cola_model = os.getenv("QUALITY_COLA_MODEL", self.quality_cola_model)
        self.nlp_inference_workers = int(
            os.getenv("NLP_INFERENCE_WORKERS", str(self.nlp_inference_workers))
        )
        self.preload_nlp_models = os.getenv(
            "PRELOAD_NLP_MODELS", "true"
        ).lower() in ("1", "true", "yes")


@lru_cache
def get_settings() -> Settings:
    return Settings()
