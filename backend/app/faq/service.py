from app.faq.data import FAQ_ENTRIES
from app.schemas.faq import FaqAskResponse, FaqEntry


def _score_entry(user_question: str, entry: FaqEntry) -> int:
    """为 FAQ 条目计算一个很简单的匹配分数。

    当前阶段我们仍然坚持“先做可解释规则，再做 AI 增强”。
    这里不引入向量检索或 LLM 语义匹配，目的是让你先看懂：
    FAQ 工具本质上也是一个可被 Agent 调用的业务工具。
    """

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
            answer="当前没有直接命中 FAQ 条目。后续我们会把这块升级成更强的检索或 Agent 问答能力。",
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
