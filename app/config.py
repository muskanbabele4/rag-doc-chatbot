import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM Provider: "openai", "anthropic", or "google" (Gemini - free tier available)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "google")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Defaults are set for the Google provider since that's free.
    # If you switch LLM_PROVIDER to "openai" or "anthropic", also set
    # LLM_MODEL / EMBEDDING_MODEL env vars to the right model names.
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")

    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./app.db")

    DOCS_UPLOAD_DIR: str = os.getenv("DOCS_UPLOAD_DIR", "./data/documents")

    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))

    N8N_WEBHOOK_SECRET: str = os.getenv("N8N_WEBHOOK_SECRET", "change-me")


settings = Settings()
