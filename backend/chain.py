import os
from dotenv import load_dotenv
load_dotenv()

from langchain_cohere import CohereEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def get_vectorstore():
    """Connect to existing Pinecone index."""
    embeddings = CohereEmbeddings(
        model="embed-english-v3.0",
        cohere_api_key=os.getenv("COHERE_API_KEY")
    )
    return PineconeVectorStore.from_existing_index(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        embedding=embeddings
    )

def get_retriever(doc_ids: list[str] = None):
    vectorstore = get_vectorstore()

    search_kwargs = {
        "k": 7,
        "fetch_k": 20,
        "lambda_mult": 0.85  # was 0.7, more relevance-focused now
    }

    if doc_ids:
        search_kwargs["filter"] = {"doc_id": {"$in": doc_ids}}

    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs
    )

def format_docs(docs):
    """Format retrieved chunks into a single context string with citations."""
    return "\n\n".join(
        f"[{doc.metadata.get('filename', 'unknown')} | page {doc.metadata.get('page', '?')}]\n{doc.page_content}"
        for doc in docs
    )

def get_chain(doc_ids: list[str] = None):
    """
    Build and return the full RAG chain.
    doc_ids: optional list to filter retrieval to specific documents.
    """
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    prompt = PromptTemplate.from_template("""<instructions>
You are a document assistant. Follow these rules strictly:
1. Answer ONLY using the context provided below.
2. If the answer is not in the context, say exactly: "The document does not contain information about this."
3. Do NOT use outside knowledge. Do NOT guess.
4. Always cite the filename and page number after every claim.
</instructions>

<context>
{context}
</context>

<question>{question}</question>

<answer>""")

    retriever = get_retriever(doc_ids)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever