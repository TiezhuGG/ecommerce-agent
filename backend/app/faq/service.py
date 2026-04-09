from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass

from app.db.models import FaqEntryRecord
from app.db.service import DatabaseUnavailableError, SQLAlchemyError, faq_from_record, session_scope
from app.db.repositories import get_repositories
from app.llm.service import (
    LLMRequestError,
    LLMServiceUnavailableError,
    request_text,
)
from app.schemas.faq import (
    FaqAskResponse,
    FaqCitation,
    FaqDeleteResponse,
    FaqEntry,
    FaqEntryImportItem,
    FaqEntryImportRequest,
    FaqEntryImportResponse,
    FaqEntryListResponse,
    FaqEntryUpsertRequest,
)


class FaqAdminUnavailableError(RuntimeError):
    """知识库管理当前不可用。"""


class FaqEntryNotFoundError(RuntimeError):
    """指定知识库条目不存在。"""


class FaqImportValidationError(RuntimeError):
    """知识库导入数据不合法。"""


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


def _generate_answer_with_llm(question: str, citations: list[FaqCitation]):
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
    return result


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
            retrieval_provider="knowledge-rag-v1-local-retrieval",
            answer_provider="knowledge-rag-v1-no-match",
        )

    try:
        llm_result = _generate_answer_with_llm(question, citations)
        answer = llm_result.text
        answer_provider = f"{llm_result.provider} / {llm_result.strategy}"
    except (LLMServiceUnavailableError, LLMRequestError):
        answer = _build_fallback_answer(question, citations, matched_entry)
        answer_provider = "knowledge-rag-v1-fallback"

    return FaqAskResponse(
        question=question,
        answer=answer,
        matched_entry=matched_entry,
        source_label=matched_entry.source_label,
        suggestions=_build_suggestions(matched_entry),
        citations=citations,
        retrieval_mode="knowledge-rag-v1",
        retrieval_provider="knowledge-rag-v1-local-retrieval",
        answer_provider=answer_provider,
    )


def _require_faq_admin_backend() -> str:
    backend = get_repositories().backend
    if not backend.startswith("sqlalchemy-"):
        raise FaqAdminUnavailableError("当前未启用数据库知识库存储，无法管理知识文档。")
    if FaqEntryRecord is None:
        raise FaqAdminUnavailableError("当前数据库知识库模型不可用。")
    return backend


def _normalize_keywords(keywords: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in keywords:
        value = item.strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(value)
    return normalized


def _build_entry_model(entry_id: str, payload: FaqEntryUpsertRequest) -> FaqEntry:
    return FaqEntry(
        id=entry_id,
        topic=payload.topic.strip(),
        question=payload.question.strip(),
        answer=payload.answer.strip(),
        source_label=payload.source_label.strip(),
        keywords=_normalize_keywords(payload.keywords),
        body=payload.body.strip(),
    )


def _build_entry_from_import_item(item: FaqEntryImportItem) -> FaqEntry:
    entry_id = (item.id or "").strip() or f"kb-{uuid.uuid4().hex[:12]}"
    return FaqEntry(
        id=entry_id,
        topic=item.topic.strip(),
        question=item.question.strip(),
        answer=item.answer.strip(),
        source_label=item.source_label.strip(),
        keywords=_normalize_keywords(item.keywords),
        body=item.body.strip(),
    )


def list_faq_entries_admin() -> FaqEntryListResponse:
    backend = _require_faq_admin_backend()

    try:
        with session_scope() as session:
            rows = (
                session.query(FaqEntryRecord)
                .order_by(FaqEntryRecord.topic.asc(), FaqEntryRecord.question.asc())
                .all()
            )
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise FaqAdminUnavailableError(f"当前无法读取知识库条目：{exc}") from exc

    return FaqEntryListResponse(
        backend=backend,
        items=[faq_from_record(row) for row in rows],
    )


def create_faq_entry(payload: FaqEntryUpsertRequest) -> FaqEntry:
    _require_faq_admin_backend()
    entry_id = f"kb-{uuid.uuid4().hex[:12]}"
    entry = _build_entry_model(entry_id, payload)

    try:
        with session_scope() as session:
            session.add(
                FaqEntryRecord(
                    id=entry.id,
                    topic=entry.topic,
                    question=entry.question,
                    answer=entry.answer,
                    source_label=entry.source_label,
                    keywords_json=json.dumps(entry.keywords, ensure_ascii=False),
                    body=entry.body,
                )
            )
            session.commit()
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise FaqAdminUnavailableError(f"当前无法新增知识库条目：{exc}") from exc

    return entry


def update_faq_entry(entry_id: str, payload: FaqEntryUpsertRequest) -> FaqEntry:
    _require_faq_admin_backend()
    entry = _build_entry_model(entry_id, payload)

    try:
        with session_scope() as session:
            row = session.get(FaqEntryRecord, entry_id)
            if row is None:
                raise FaqEntryNotFoundError(f"未找到 entry_id={entry_id} 对应的知识库条目。")

            row.topic = entry.topic
            row.question = entry.question
            row.answer = entry.answer
            row.source_label = entry.source_label
            row.keywords_json = json.dumps(entry.keywords, ensure_ascii=False)
            row.body = entry.body
            session.commit()
    except FaqEntryNotFoundError:
        raise
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise FaqAdminUnavailableError(f"当前无法更新知识库条目：{exc}") from exc

    return entry


def delete_faq_entry(entry_id: str) -> FaqDeleteResponse:
    _require_faq_admin_backend()

    try:
        with session_scope() as session:
            row = session.get(FaqEntryRecord, entry_id)
            if row is None:
                raise FaqEntryNotFoundError(f"未找到 entry_id={entry_id} 对应的知识库条目。")
            session.delete(row)
            session.commit()
    except FaqEntryNotFoundError:
        raise
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise FaqAdminUnavailableError(f"当前无法删除知识库条目：{exc}") from exc

    return FaqDeleteResponse(entry_id=entry_id)


def export_faq_entries() -> FaqEntryListResponse:
    return list_faq_entries_admin()


def import_faq_entries(payload: FaqEntryImportRequest) -> FaqEntryImportResponse:
    backend = _require_faq_admin_backend()
    mode = payload.mode.strip().lower() or "upsert"
    if mode not in {"upsert", "replace"}:
        raise FaqImportValidationError("导入模式仅支持 upsert 或 replace。")
    if not payload.items:
        raise FaqImportValidationError("导入内容不能为空。")

    entries = [_build_entry_from_import_item(item) for item in payload.items]
    duplicate_ids = {entry.id for entry in entries if sum(1 for current in entries if current.id == entry.id) > 1}
    if duplicate_ids:
        raise FaqImportValidationError(f"导入数据存在重复 entry_id：{', '.join(sorted(duplicate_ids))}")

    created_count = 0
    updated_count = 0

    try:
        with session_scope() as session:
            if mode == "replace":
                session.query(FaqEntryRecord).delete()
                for entry in entries:
                    session.add(
                        FaqEntryRecord(
                            id=entry.id,
                            topic=entry.topic,
                            question=entry.question,
                            answer=entry.answer,
                            source_label=entry.source_label,
                            keywords_json=json.dumps(entry.keywords, ensure_ascii=False),
                            body=entry.body,
                        )
                    )
                created_count = len(entries)
                session.commit()
            else:
                for entry in entries:
                    row = session.get(FaqEntryRecord, entry.id)
                    if row is None:
                        session.add(
                            FaqEntryRecord(
                                id=entry.id,
                                topic=entry.topic,
                                question=entry.question,
                                answer=entry.answer,
                                source_label=entry.source_label,
                                keywords_json=json.dumps(entry.keywords, ensure_ascii=False),
                                body=entry.body,
                            )
                        )
                        created_count += 1
                    else:
                        row.topic = entry.topic
                        row.question = entry.question
                        row.answer = entry.answer
                        row.source_label = entry.source_label
                        row.keywords_json = json.dumps(entry.keywords, ensure_ascii=False)
                        row.body = entry.body
                        updated_count += 1
                session.commit()
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise FaqAdminUnavailableError(f"当前无法导入知识库条目：{exc}") from exc

    return FaqEntryImportResponse(
        mode=mode,
        imported_count=len(entries),
        created_count=created_count,
        updated_count=updated_count,
        backend=backend,
    )
