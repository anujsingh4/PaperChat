# backend/ingest.py
import os
import hashlib
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

def get_file_hash(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def load_document(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        loader = PyMuPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return loader.load()

def chunk_documents(documents, filename: str, doc_id: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(documents)
    for i, chunk in enumerate(chunks):
        chunk.metadata.update({
            "doc_id": doc_id,
            "filename": filename,
            "chunk_index": i,
            "page": chunk.metadata.get("page", 0)
        })
    return chunks

def is_already_indexed(doc_id: str) -> bool:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
    results = index.query(
        vector=[0.0] * 1024,
        top_k=1,
        filter={"doc_id": {"$eq": doc_id}},
        include_metadata=True
    )
    return len(results["matches"]) > 0

def ingest_file(file_path: str) -> dict:
    filename = os.path.basename(file_path)
    doc_id = get_file_hash(file_path)

    if is_already_indexed(doc_id):
        print(f"Skipping '{filename}' — already indexed")
        return {"doc_id": doc_id, "filename": filename, "chunks": 0, "skipped": True}

    print(f"Indexing '{filename}'...")
    documents = load_document(file_path)
    print(f"  Loaded {len(documents)} pages/sections")

    chunks = chunk_documents(documents, filename, doc_id)
    print(f"  Split into {len(chunks)} chunks")

    embeddings = CohereEmbeddings(
        model="embed-english-v3.0",
        cohere_api_key=os.getenv("COHERE_API_KEY")
    )

    PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=os.getenv("PINECONE_INDEX_NAME")
    )

    print(f"  Stored {len(chunks)} chunks in Pinecone")
    return {"doc_id": doc_id, "filename": filename, "chunks": len(chunks), "skipped": False}