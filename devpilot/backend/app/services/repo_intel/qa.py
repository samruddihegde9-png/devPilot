"""
"Ask DevPilot" question answering.

Retrieval is a simple, dependency-free keyword-overlap ranker (no vector
store, no embeddings API) over chunks of the already-scanned files. That
keeps this fully offline-capable and easy to audit: every ranked chunk is
literally a slice of a real file at a real line range.

If `OPENAI_API_KEY` is configured, the top chunks are handed to the model
with an explicit instruction to answer only from them and say so when they
don't contain the answer. If no key is configured (or the call fails), a
deterministic answer is built directly from the retrieved chunks instead —
grounded either way, never fabricated.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.repo_intel.llm import call_llm
from app.services.repo_intel.scanner import ScanResult
from app.schemas.repo_intel import AskResponse, UsedSnippet

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "to", "of", "in",
    "on", "for", "and", "or", "how", "what", "where", "when", "which", "does",
    "do", "this", "that", "it", "with", "as", "at", "by", "from", "up", "into",
    "happens", "happen", "should", "would", "could", "i", "my", "we", "our",
}

_CHUNK_LINES = 40
_CHUNK_OVERLAP = 8
_TOP_K = 5

_SYSTEM_PROMPT = (
    "You are DevPilot's repository assistant. Answer the developer's question "
    "using ONLY the numbered file excerpts provided below — they are the "
    "actual contents of files in their project. Cite file paths (e.g. "
    "`app/api/files.py`) inline when you reference something from an excerpt. "
    "If the excerpts don't contain enough information to answer confidently, "
    "say so plainly instead of guessing or inventing file/function names that "
    "aren't shown."
)


@dataclass
class Chunk:
    path: str
    start_line: int
    end_line: int
    text: str


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{1,}", text.lower()) if t not in _STOPWORDS]


def _chunk_file(path: str, content: str) -> list[Chunk]:
    lines = content.splitlines()
    if not lines:
        return []
    chunks = []
    step = max(1, _CHUNK_LINES - _CHUNK_OVERLAP)
    for start in range(0, len(lines), step):
        end = min(start + _CHUNK_LINES, len(lines))
        chunks.append(
            Chunk(path=path, start_line=start + 1, end_line=end, text="\n".join(lines[start:end]))
        )
        if end == len(lines):
            break
    return chunks


def _score(chunk: Chunk, question_tokens: set[str], question: str) -> float:
    body_tokens = _tokenize(chunk.text)
    if not body_tokens:
        return 0.0
    body_set = set(body_tokens)
    overlap = len(question_tokens & body_set)
    score = float(overlap)

    # Small bonus when the question mentions something in the file's path
    # (e.g. "authentication" question hitting a file with "auth" in its name).
    path_tokens = set(_tokenize(chunk.path.replace("/", " ").replace("_", " ").replace(".", " ")))
    score += 1.5 * len(question_tokens & path_tokens)

    # Bonus for def/class/function declarations naming something in the question.
    for line in chunk.text.splitlines():
        if re.match(r"\s*(def|class|function|const|export)\s", line):
            decl_tokens = set(_tokenize(line))
            score += 0.5 * len(question_tokens & decl_tokens)

    return score


def retrieve(scan: ScanResult, question: str, top_k: int = _TOP_K) -> list[Chunk]:
    question_tokens = set(_tokenize(question))
    if not question_tokens:
        return []

    all_chunks: list[Chunk] = []
    for f in scan.files:
        all_chunks.extend(_chunk_file(f.path, f.content))

    scored = [(chunk, _score(chunk, question_tokens, question)) for chunk in all_chunks]
    scored = [(c, s) for c, s in scored if s > 0]
    scored.sort(key=lambda pair: -pair[1])
    return [c for c, _ in scored[:top_k]]


def _deterministic_answer(question: str, chunks: list[Chunk]) -> str:
    if not chunks:
        return (
            "I couldn't find anything in the scanned repository that looks relevant to that "
            "question. Try rephrasing it, or mention a specific file/feature name."
        )
    intro = (
        "No AI model is configured (set `OPENAI_API_KEY` to get a written answer), so here are "
        "the most relevant excerpts from the repository for your question:"
    )
    parts = [intro]
    for c in chunks:
        parts.append(f"\n**{c.path}** (lines {c.start_line}-{c.end_line}):\n```\n{c.text.strip()[:800]}\n```")
    return "\n".join(parts)


def ask(scan: ScanResult, question: str) -> AskResponse:
    chunks = retrieve(scan, question)
    used = [UsedSnippet(path=c.path, start_line=c.start_line, end_line=c.end_line, snippet=c.text[:600]) for c in chunks]

    if not chunks:
        return AskResponse(
            answer=_deterministic_answer(question, chunks),
            mode="none",
            used_files=used,
        )

    context = "\n\n".join(
        f"[{i + 1}] {c.path} (lines {c.start_line}-{c.end_line}):\n{c.text}" for i, c in enumerate(chunks)
    )
    llm_answer = call_llm(_SYSTEM_PROMPT, f"Question: {question}\n\nFile excerpts:\n{context}", max_tokens=500)

    if llm_answer:
        return AskResponse(answer=llm_answer, mode="ai", used_files=used)
    return AskResponse(answer=_deterministic_answer(question, chunks), mode="retrieval", used_files=used)
