import os
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings

LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".docx": Docx2txtLoader,
}


def get_embeddings():
    if settings.LLM_PROVIDER == "google":
        return GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )
    return OpenAIEmbeddings(model=settings.EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)


def get_vectorstore() -> Chroma:
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    return Chroma(
        collection_name="documents",
        embedding_function=get_embeddings(),
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )


def load_document(file_path: str) -> List:
    ext = os.path.splitext(file_path)[1].lower()
    loader_cls = LOADER_MAP.get(ext)
    if not loader_cls:
        raise ValueError(f"Unsupported file type: {ext}")
    return loader_cls(file_path).load()


def chunk_documents(docs: List) -> List:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    return splitter.split_documents(docs)


def ingest_file(file_path: str) -> int:
    """Loads, chunks, embeds and stores a single document. Returns chunk count."""
    docs = load_document(file_path)
    chunks = chunk_documents(docs)
    if not chunks:
        return 0

    filename = os.path.basename(file_path)
    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = filename
        chunk.metadata["chunk_id"] = i

    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)
    return len(chunks)
