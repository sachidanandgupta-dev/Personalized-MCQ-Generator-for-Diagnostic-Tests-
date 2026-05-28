import re

DEFAULT_CHUNK_SIZE = 8_000
DEFAULT_MAX_FOR_MCQ = 10_000


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[str]:
    """Split text into chunks at paragraph boundaries when possible."""
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    if len(normalized) <= chunk_size:
        return [normalized]

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", normalized) if p.strip()]
    if not paragraphs:
        return _split_by_size(normalized, chunk_size)

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        para_len = len(paragraph) + 2
        if para_len > chunk_size:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0
            chunks.extend(_split_by_size(paragraph, chunk_size))
            continue

        if current_len + para_len > chunk_size and current:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_len = len(paragraph)
        else:
            current.append(paragraph)
            current_len += para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def _split_by_size(text: str, chunk_size: int) -> list[str]:
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def select_text_for_mcq(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_length: int = DEFAULT_MAX_FOR_MCQ,
) -> tuple[str, dict]:
    """
    Chunk long documents and return the first chunk (trimmed) for MCQ generation.
    Returns selected text and metadata about chunking.
    """
    chunks = chunk_text(text, chunk_size=chunk_size)
    selected = chunks[0]
    if len(selected) > max_length:
        selected = selected[:max_length].rstrip()

    return selected, {
        "total_chunks": len(chunks),
        "chunk_index_used": 0,
        "extracted_char_count": len(text),
        "used_char_count": len(selected),
    }
