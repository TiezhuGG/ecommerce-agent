from __future__ import annotations

import re
from dataclasses import dataclass

from app.db.repositories import get_repositories
from app.llm.service import (
    LLMRequestError,
    LLMServiceUnavailableError,
    request_text,
)
from app.schemas.faq import FaqAskResponse, FaqCitation, FaqEntry


@dataclass(slots=True)
class KnowledgeChunk:
    """A searchable chunk extracted from a knowledge entry."""

    entry: FaqEntry
    text: str
    chunk_index: int


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text.strip().lower())


def _build_bigrams(text: str) -> set[str]:
    normalized = _normalize_text(text)
    if len(normalized) < 2:
        return {normalized} if normalized else set()
    return {normalized[index : index + 2] for index in range(len(normalized) - 1)}


def _build_chunks(entry: FaqEntry) -> list[KnowledgeChunk]:
    parts = [entry.answer]
    parts.extend(part.strip() for part in entry.body.split("\n\n") if part.strip())
    return [
        KnowledgeChunk(entry=entry, text=part, chunk_index=index)
        for index, part in enumerate(parts)
    ]


def _score_chunk(user_question: str, chunk: KnowledgeChunk) -> float:
    normalized_question = _normalize_text(user_question)
    if not normalized_question:
        return 0.0

    entry = chunk.entry
    score = 0.0
    normalized_entry_question = _normalize_text(entry.question)

    if normalized_question in normalized_entry_question or normalized_entry_question in normalized_question:
        score += 8.0

    topic = _normalize_text(entry.topic)
    if topic and topic in normalized_question:
        score += 1.5

    chunk_text = _normalize_text(chunk.text)
    for keyword in entry.keywords:
        normalized_keyword = _normalize_text(keyword)
        if normalized_keyword and normalized_keyword in normalized_question:
            score += 3.0
            if normalized_keyword in chunk_text:
                score += 1.0

    overlap = len(_build_bigrams(user_question) & _build_bigrams(chunk.text))
    score += min(overlap * 0.35, 6.0)

    return round(score, 2)


def _retrieve_citations(user_question: str) -> list[FaqCitation]:
    scored_chunks: list[tuple[KnowledgeChunk, float]] = []
    for entry in get_repositories().faq.list_entries():
        for chunk in _build_chunks(entry):
            score = _score_chunk(user_question, chunk)
            if score > 0:
                scored_chunks.append((chunk, score))

    scored_chunks.sort(key=lambda item: item[1], reverse=True)

    best_chunk_by_entry: dict[str, tuple[KnowledgeChunk, float]] = {}
    for chunk, score in scored_chunks:
        current = best_chunk_by_entry.get(chunk.entry.id)
        if current is None or score > current[1]:
            best_chunk_by_entry[chunk.entry.id] = (chunk, score)

    ranked_chunks = sorted(best_chunk_by_entry.values(), key=lambda item: item[1], reverse=True)
    if not ranked_chunks:
        return []

    top_score = ranked_chunks[0][1]
    min_score = max(1.0, round(top_score * 0.15, 2))
    top_chunks = [item for item in ranked_chunks if item[1] >= min_score][:3]
    return [
        FaqCitation(
            entry_id=chunk.entry.id,
            title=chunk.entry.question,
            snippet=chunk.text[:160],
            source_label=chunk.entry.source_label,
            score=score,
        )
        for chunk, score in top_chunks
    ]


def _select_matched_entry(citations: list[FaqCitation]) -> FaqEntry | None:
    if not citations:
        return None

    entry_map = {entry.id: entry for entry in get_repositories().faq.list_entries()}
    return entry_map.get(citations[0].entry_id)


def _build_suggestions(matched_entry: FaqEntry | None) -> list[str]:
    return [
        entry.question
        for entry in get_repositories().faq.list_entries()
        if matched_entry is None or entry.id != matched_entry.id
    ][:3]


def _build_fallback_answer(
    question: str,
    citations: list[FaqCitation],
    matched_entry: FaqEntry | None,
) -> str:
    if not citations or not matched_entry:
        return "当前知识库里没有命中足够相关的内容。你可以换一种问法，或者把问题说得更具体一些。"

    citation_lines = "\n".join(f"- {citation.snippet}" for citation in citations[:2])
    return (
        f"{matched_entry.answer}\n\n"
        "我是基于以下知识片段整理出的回答：\n"
        f"{citation_lines}\n\n"
        f"如果你还想继续追问“{question}”相关细节，我可以继续基于这批知识片段展开说明。"
    )


def _generate_answer_with_llm(question: str, citations: list[FaqCitation]) -> str:
    citation_text = "\n\n".join(
        (
            f"片段 {index + 1}\n"
            f"标题：{citation.title}\n"
            f"来源：{citation.source_label}\n"
            f"内容：{citation.snippet}"
        )
        for index, citation in enumerate(citations)
    )

    result = request_text(
        system_prompt=(
            "你是电商售前知识库助手。"
            "你只能基于给定的知识片段回答，不要编造政策、库存、物流时效或额外规则。"
            "如果知识片段不足以支撑结论，就直接说明当前知识库没有明确答案。"
        ),
        user_prompt=(
            f"用户问题：{question}\n\n"
            f"知识片段：\n{citation_text}\n\n"
            "请输出一段简洁中文回答，优先给出结论，再补一句必要说明。"
        ),
    )
    return result.text


def ask_faq(question: str) -> FaqAskResponse:
    citations = _retrieve_citations(question)
    matched_entry = _select_matched_entry(citations)

    if not matched_entry:
        return FaqAskResponse(
            question=question,
            answer="当前知识库里没有命中足够相关的内容。你可以换一种问法，或者把问题说得更具体一些。",
            matched_entry=None,
            source_label="知识库未命中",
            suggestions=_build_suggestions(None),
            citations=[],
            retrieval_mode="knowledge-rag-v1",
        )

    try:
        answer = _generate_answer_with_llm(question, citations)
    except (LLMServiceUnavailableError, LLMRequestError):
        answer = _build_fallback_answer(question, citations, matched_entry)

    return FaqAskResponse(
        question=question,
        answer=answer,
        matched_entry=matched_entry,
        source_label=matched_entry.source_label,
        suggestions=_build_suggestions(matched_entry),
        citations=citations,
        retrieval_mode="knowledge-rag-v1",
    )
