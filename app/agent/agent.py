from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.rag.retriever import search_documents
from app.db.database import SessionLocal
from app.db.models import Document


def get_llm():
    """Swappable LLM provider — matches JD requirement of integrating
    OpenAI / Azure OpenAI / Anthropic / open-source models."""
    if settings.LLM_PROVIDER == "anthropic":
        return ChatAnthropic(model=settings.LLM_MODEL, api_key=settings.ANTHROPIC_API_KEY)
    return ChatOpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0)


@tool
def search_company_documents(query: str) -> str:
    """Search the uploaded company documents (RAG) to answer a question.
    Use this whenever the user asks something that might be answered
    by internal documents/PDFs that have been ingested into the system."""
    results = search_documents(query, k=4)
    if not results:
        return "No relevant documents found in the knowledge base."
    formatted = [
        f"[Source: {r.metadata.get('source', 'unknown')}]\n{r.page_content}"
        for r in results
    ]
    return "\n\n".join(formatted)


@tool
def list_uploaded_documents() -> str:
    """List all documents currently ingested into the knowledge base,
    along with chunk counts and processing status. Use this for
    questions like 'what documents do you have access to'."""
    db: Session = SessionLocal()
    try:
        docs = db.query(Document).all()
        if not docs:
            return "No documents have been uploaded yet."
        return "\n".join(
            f"{d.filename} ({d.file_type}) - {d.chunk_count} chunks - {d.status}"
            for d in docs
        )
    finally:
        db.close()


TOOLS = [search_company_documents, list_uploaded_documents]

SYSTEM_PROMPT = """You are an internal AI assistant that answers questions
about a company's uploaded documents. Always try the
`search_company_documents` tool first when the question could relate to
uploaded documents. If the answer isn't found in the documents, say so
honestly instead of guessing. Be concise and mention the source filename
when you use document content."""


def build_agent_executor() -> AgentExecutor:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=TOOLS, verbose=False)
