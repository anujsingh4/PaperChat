# backend/main.py
import os
import json
import asyncio
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import shutil
from pinecone import Pinecone

from backend.ingest import ingest_file
from backend.chain import get_chain

app = FastAPI(title="RAG Assistant API")

# CORS — allows React dev server to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://localhost:3000",
                    "https://rag-assistant-theta.vercel.app", 
                    "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request/Response models ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    doc_ids: list[str] = []   # empty = search all documents

# ─── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "RAG Assistant API is running"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Accept a PDF or DOCX, save temporarily, run ingestion pipeline.
    Returns doc_id and chunk count.
    """
    # Validate file type
    allowed = [".pdf", ".docx"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Only PDF and DOCX files allowed. Got: {ext}")

    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run ingestion
    result = ingest_file(temp_path)

    # Clean up temp file
    os.remove(temp_path)

    return {
        "message": "File processed successfully" if not result["skipped"] else "File already indexed",
        "doc_id": result["doc_id"],
        "filename": result["filename"],
        "chunks": result["chunks"],
        "skipped": result["skipped"]
    }


@app.get("/documents")
def list_documents():
    """
    List all indexed documents by querying Pinecone metadata.
    """
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

    # Fetch a sample of vectors to extract unique documents
    results = index.query(
        vector=[0.0] * 1024,
        top_k=100,
        include_metadata=True
    )

    # Deduplicate by doc_id
    seen = {}
    for match in results["matches"]:
        meta = match.get("metadata", {})
        doc_id = meta.get("doc_id")
        if doc_id and doc_id not in seen:
            seen[doc_id] = {
                "doc_id": doc_id,
                "filename": meta.get("filename", "unknown")
            }

    return {"documents": list(seen.values())}


@app.delete("/document/{doc_id}")
def delete_document(doc_id: str):
    """
    Delete all vectors for a given doc_id from Pinecone.
    """
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

    index.delete(filter={"doc_id": {"$eq": doc_id}})

    return {"message": f"Document {doc_id} deleted successfully"}


@app.post("/chat")
async def chat(request: ChatRequest):
    async def stream_response():
        chain, retriever = get_chain(
            doc_ids=request.doc_ids if request.doc_ids else None
        )

        source_docs = retriever.invoke(request.question)

        async for token in chain.astream(request.question):
            if token:
                yield f"data: {json.dumps({'token': token})}\n\n"
                await asyncio.sleep(0)

        sources = []
        seen_sources = set()
        for doc in source_docs:
            key = f"{doc.metadata.get('filename')}_{doc.metadata.get('page')}"
            if key not in seen_sources:
                seen_sources.add(key)
                sources.append({
                    "filename": doc.metadata.get("filename", "unknown"),
                    "page": doc.metadata.get("page", "?")
                })

        yield f"data: {json.dumps({'sources': sources})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )