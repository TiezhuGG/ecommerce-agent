from app.faq.data import FAQ_ENTRIES
from app.schemas.faq import FaqAskResponse, FaqEntry


def _score_entry(user_question: str, entry: FaqEntry) -> int:
    """为 FAQ 条目计算一个简单匹配分数。"""

    normalized_question = user_question.strip().lower()
    score = 0

    if entry.question.lower() in normalized_question or normalized_question in entry.question.lower():
        score += 5

    for keyword in entry.keywords:
        if keyword.lower() in normalized_question:
            score += 2

    if entry.topic.lower() in normalized_question:
        score += 1

    return score


def ask_faq(question: str) -> FaqAskResponse:
    """根据用户问题匹配最相关的 FAQ 条目。"""

    ranked_entries = sorted(
        FAQ_ENTRIES,
        key=lambda entry: _score_entry(question, entry),
        reverse=True,
    )

    best_entry = ranked_entries[0] if ranked_entries else None
    best_score = _score_entry(question, best_entry) if best_entry else 0

    if not best_entry or best_score == 0:
        return FaqAskResponse(
            question=question,
            answer="当前没有直接命中的 FAQ 条目。后续我们会把这一块升级成知识库检索或更完整的 Agent 问答。",
            matched_entry=None,
            source_label="FAQ 占位回复",
            suggestions=[entry.question for entry in FAQ_ENTRIES[:3]],
        )

    return FaqAskResponse(
        question=question,
        answer=best_entry.answer,
        matched_entry=best_entry,
        source_label=best_entry.source_label,
        suggestions=[entry.question for entry in ranked_entries[1:4]],
    )
