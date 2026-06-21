import os
import shutil
from typing import List

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import init_db, get_db
from app.db import models
from app.schemas import ChatRequest, ChatResponse, DocumentInfo, ChatHistoryItem
from app.rag.ingest import ingest_file
from app.agent.agent import build_agent_executor

app = FastAPI(title="Document Q&A RAG Agent", version="1.0.0")


@app.on_event("startup")
def on_startup():
    os.makedirs(settings.DOCS_UPLOAD_DIR, exist_ok=True)
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents/upload", response_model=DocumentInfo)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".txt", ".docx"):
        raise HTTPException(400, f"Unsupported file type: {ext}")

    save_path = os.path.join(settings.DOCS_UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = models.Document(filename=file.filename, file_type=ext, status="processing")
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        chunk_count = ingest_file(save_path)
        doc.chunk_count = chunk_count
        doc.status = "processed"
    except Exception as e:
        doc.status = "failed"
        db.commit()
        raise HTTPException(500, f"Ingestion failed: {e}")

    db.commit()
    db.refresh(doc)
    return doc


@app.get("/documents", response_model=List[DocumentInfo])
def list_documents(db: Session = Depends(get_db)):
    return db.query(models.Document).all()


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    user_msg = models.ChatMessage(session_id=req.session_id, role="user", content=req.message)
    db.add(user_msg)
    db.commit()

    agent_executor = build_agent_executor()
    result = agent_executor.invoke({"input": req.message})
    answer = result.get("output", "")

    assistant_msg = models.ChatMessage(session_id=req.session_id, role="assistant", content=answer)
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(session_id=req.session_id, answer=answer)


@app.get("/chat/{session_id}/history", response_model=List[ChatHistoryItem])
def chat_history(session_id: str, db: Session = Depends(get_db)):
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.created_at)
        .all()
    )


@app.post("/n8n/ingest-webhook")
def n8n_ingest_webhook(
    file_path: str,
    secret: str = Header(None, alias="X-N8N-Secret"),
    db: Session = Depends(get_db),
):
    """Called by the n8n workflow whenever a new document lands in the
    watched folder, so ingestion happens automatically without a manual
    upload through the API."""
    if secret != settings.N8N_WEBHOOK_SECRET:
        raise HTTPException(401, "Invalid webhook secret")
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    doc = models.Document(filename=filename, file_type=ext, status="processing")
    db.add(doc)
    db.commit()
    db.refresh(doc)

    chunk_count = ingest_file(file_path)
    doc.chunk_count = chunk_count
    doc.status = "processed"
    db.commit()

    return {"filename": filename, "chunks": chunk_count}
