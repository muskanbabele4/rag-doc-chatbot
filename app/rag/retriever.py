from app.rag.ingest import get_vectorstore


def get_retriever(k: int = 4):
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": k})


def search_documents(query: str, k: int = 4):
    retriever = get_retriever(k=k)
    return retriever.invoke(query)
