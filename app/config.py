import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM Provider: "openai" or "anthropic" (matches JD: OpenAI / Azure OpenAI / Anthropic / open-source)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./app.db")

    DOCS_UPLOAD_DIR: str = os.getenv("DOCS_UPLOAD_DIR", "./data/documents")

    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))

    N8N_WEBHOOK_SECRET: str = os.getenv("N8N_WEBHOOK_SECRET", "change-me")


settings = Settings()
