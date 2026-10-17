"""Document ingestion and prompt-injection hygiene service (P2 ownership).

Handles document parsing, chunking, and sanitization per BE-4 of Kyro Team Bible.
"""

import re
from typing import Any, Dict, List
from uuid import UUID

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"system\s*prompt",
    r"you\s+are\s+now",
    r"mark\s+this\s+vendor\s+compliant",
    r"disregard\s+(the\s+)?above",
    r"override\s+(all\s+)?rules",
]


def detect_suspicious_patterns(text: str) -> bool:
    """Detect obvious instruction-like / prompt-injection patterns in untrusted vendor text."""
    lower_text = text.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower_text):
            return True
    return False


def clean_untrusted_text(text: str) -> str:
    """Strip control characters and normalize untrusted text."""
    # Remove control characters except standard whitespace
    cleaned = "".join(ch for ch in text if ch.isprintable() or ch in "\n\r\t")
    return cleaned.strip()


def chunk_text(text: str, chunk_size_words: int = 400, overlap_words: int = 50) -> List[Dict[str, Any]]:
    """Chunk text into token-approximate windows preserving index and suspicious flags."""
    words = text.split()
    chunks = []
    chunk_index = 0
    start = 0

    while start < len(words):
        end = min(start + chunk_size_words, len(words))
        chunk_content = " ".join(words[start:end])
        is_suspicious = detect_suspicious_patterns(chunk_content)

        chunks.append({
            "chunk_index": chunk_index,
            "content": chunk_content,
            "token_count": len(chunk_content) // 4,  # Approximate tokens
            "is_suspicious": is_suspicious,
        })
        chunk_index += 1
        if end >= len(words):
            break
        start += (chunk_size_words - overlap_words)

    return chunks


async def enqueue(document_id: UUID) -> str:
    """Enqueue a document for asynchronous ingestion."""
    # Worker job queue placeholder (Redis RQ / arq)
    return f"enqueued_job_{document_id}"
