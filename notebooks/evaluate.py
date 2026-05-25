# notebooks/evaluate.py - Manual RAG Evaluation
import sys
import os
sys.path.insert(0, "/Users/anuj/Desktop/PJ/rag-assistant")

from dotenv import load_dotenv
load_dotenv("/Users/anuj/Desktop/PJ/rag-assistant/.env")

from langchain_groq import ChatGroq
from backend.chain import get_chain, get_retriever

# ─── Config ───────────────────────────────────────────────────────────────
DOC_ID = "7aaa8639f8e07aa66ff10c27834895cb"  # from browser console

TEST_CASES = [
    {
        "question": "what is the name of supervisor in Internship report anuj singh?",
        "expected_keywords": ["topic", "about", "study", "research"]
    },
    {
        "question": "what is the name of internal mentor in Internship report?",
        "expected_keywords": ["method", "approach", "technique", "used", "model"]
    },
    {
        "question": "What were the key findings or results?",
        "expected_keywords": ["result", "finding", "accuracy", "performance", "conclusion"]
    },
    {
        "question": "what are the tools mentioned in intern report?",
        "expected_keywords": ["python", "model", "framework", "library", "tool", "using"]
    },
    {
        "question": "what is the name of company in intern report?",
        "expected_keywords": ["conclude", "conclusion", "future", "summary", "result"]
    },
]

# ─── Evaluation functions ──────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

def evaluate_faithfulness(answer: str, contexts: list[str]) -> float:
    """Ask LLM if every claim in the answer is supported by the context."""
    context_str = "\n\n".join(contexts)
    prompt = f"""Given this context:
{context_str}

And this answer:
{answer}

Rate from 0.0 to 1.0: How much of the answer is supported by the context?
1.0 = every claim is in the context
0.0 = answer is completely made up

Reply with ONLY a number between 0.0 and 1.0"""

    result = llm.invoke(prompt).content.strip()
    try:
        return float(result)
    except:
        return 0.5

def evaluate_relevancy(question: str, answer: str) -> float:
    """Ask LLM if the answer actually addresses the question."""
    prompt = f"""Question: {question}
Answer: {answer}

Rate from 0.0 to 1.0: How well does the answer address the question?
1.0 = perfectly answers the question
0.0 = completely irrelevant

Reply with ONLY a number between 0.0 and 1.0"""

    result = llm.invoke(prompt).content.strip()
    try:
        return float(result)
    except:
        return 0.5

def evaluate_context_precision(question: str, contexts: list[str]) -> float:
    """Check what fraction of retrieved chunks are actually relevant."""
    relevant = 0
    for ctx in contexts:
        prompt = f"""Question: {question}
Context chunk: {ctx[:500]}

Is this context chunk relevant to answering the question?
Reply with ONLY 'yes' or 'no'"""
        result = llm.invoke(prompt).content.strip().lower()
        if "yes" in result:
            relevant += 1
    return relevant / len(contexts) if contexts else 0

# ─── Run evaluation ────────────────────────────────────────────────────────
print("="*55)
print("RAG EVALUATION REPORT")
print("="*55)

chain, retriever = get_chain(doc_ids=[DOC_ID])

all_faithfulness = []
all_relevancy = []
all_precision = []

for i, test in enumerate(TEST_CASES, 1):
    question = test["question"]
    print(f"\n[{i}/5] {question}")

    # Get retrieved chunks and answer
    docs = retriever.invoke(question)
    contexts = [doc.page_content for doc in docs]
    answer = chain.invoke(question)

    print(f"Answer: {answer[:120]}...")

    # Score each metric
    faith = evaluate_faithfulness(answer, contexts)
    relev = evaluate_relevancy(question, answer)
    prec  = evaluate_context_precision(question, contexts)

    all_faithfulness.append(faith)
    all_relevancy.append(relev)
    all_precision.append(prec)

    print(f"Faithfulness: {faith:.2f} | Relevancy: {relev:.2f} | Precision: {prec:.2f}")

# ─── Final scores ──────────────────────────────────────────────────────────
avg_faith = sum(all_faithfulness) / len(all_faithfulness)
avg_relev = sum(all_relevancy) / len(all_relevancy)
avg_prec  = sum(all_precision) / len(all_precision)
overall   = (avg_faith + avg_relev + avg_prec) / 3

print("\n" + "="*55)
print("FINAL SCORES")
print("="*55)
print(f"Faithfulness:      {avg_faith:.3f}  (hallucination check)")
print(f"Answer Relevancy:  {avg_relev:.3f}  (addresses the question)")
print(f"Context Precision: {avg_prec:.3f}  (retrieval quality)")
print(f"Overall Score:     {overall:.3f}")
print("="*55)
print("\nSave these scores for your README and interviews!")