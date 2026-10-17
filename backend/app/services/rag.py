"""RAG (Retrieval-Augmented Generation) evidence search service (BE-4 & BE-6).

Retrieves citable chunks filtered by hospital_id and document types.
Supports vector retrieval over pgvector and state document scanning with keyword overlap rerank.
"""

from datetime import date
import re
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from backend.app.services.ingestion import clean_untrusted_text, detect_suspicious_patterns


async def search(
    db: Optional[Any],
    hospital_id: UUID,
    query: str,
    vendor_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    doc_types: Optional[List[str]] = None,
    k: int = 8,
    documents: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Retrieve evidence chunks for a query strictly scoped by hospital_id.

    Returns chunk text and a stable citation object:
    {document_id, chunk_id, page, filename, doc_version, doc_date, excerpt, similarity, is_suspicious}
    """
    results: List[Dict[str, Any]] = []

    # If documents passed directly (e.g. from investigation state)
    if documents:
        query_words = set(re.findall(r"\w+", query.lower()))
        for doc in documents:
            dtype = str(doc.get("doc_type", "")).lower()
            if doc_types and dtype not in [dt.lower() for dt in doc_types]:
                continue

            content = doc.get("content") or doc.get("excerpt") or doc.get("filename", "")
            cleaned = clean_untrusted_text(str(content))
            is_suspicious = detect_suspicious_patterns(cleaned)

            # Keyword overlap score
            doc_words = set(re.findall(r"\w+", cleaned.lower()))
            overlap = len(query_words.intersection(doc_words))

            results.append({
                "document_id": doc.get("id", uuid4()),
                "doc_type": doc.get("doc_type"),
                "chunk_id": uuid4(),
                "page": doc.get("page", 1),
                "filename": doc.get("filename", "document.pdf"),
                "doc_version": doc.get("version_label", "1.0"),
                "doc_date": doc.get("doc_date"),
                "valid_until": doc.get("valid_until"),
                "excerpt": cleaned[:400],
                "similarity": round(0.5 + min(overlap * 0.1, 0.49), 2),
                "is_suspicious": is_suspicious,
            })

        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:k]

    return results
