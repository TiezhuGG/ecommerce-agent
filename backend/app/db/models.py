from __future__ import annotations

SQLALCHEMY_AVAILABLE = True

try:
    from sqlalchemy import Integer, Text
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    SQLALCHEMY_AVAILABLE = False

    class DeclarativeBase:  # type: ignore[no-redef]
        pass

    class Base(DeclarativeBase):
        metadata = None

    ProductRecord = None
    FaqEntryRecord = None
    AgentRunRecord = None
else:
    class Base(DeclarativeBase):
        pass


    class ProductRecord(Base):
        __tablename__ = "products"

        id: Mapped[str] = mapped_column(Text, primary_key=True)
        name: Mapped[str] = mapped_column(Text, nullable=False)
        category: Mapped[str] = mapped_column(Text, nullable=False, index=True)
        brand: Mapped[str] = mapped_column(Text, nullable=False, index=True)
        price: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
        price_note: Mapped[str] = mapped_column(Text, nullable=False)
        summary: Mapped[str] = mapped_column(Text, nullable=False)
        scenario: Mapped[str] = mapped_column(Text, nullable=False)
        tags_json: Mapped[str] = mapped_column(Text, nullable=False)
        specs_json: Mapped[str] = mapped_column(Text, nullable=False)
        official_url: Mapped[str] = mapped_column(Text, nullable=False)


    class FaqEntryRecord(Base):
        __tablename__ = "faq_entries"

        id: Mapped[str] = mapped_column(Text, primary_key=True)
        topic: Mapped[str] = mapped_column(Text, nullable=False, index=True)
        question: Mapped[str] = mapped_column(Text, nullable=False)
        answer: Mapped[str] = mapped_column(Text, nullable=False)
        source_label: Mapped[str] = mapped_column(Text, nullable=False)
        keywords_json: Mapped[str] = mapped_column(Text, nullable=False)
        body: Mapped[str] = mapped_column(Text, nullable=False)


    class AgentRunRecord(Base):
        __tablename__ = "agent_runs"

        id: Mapped[str] = mapped_column(Text, primary_key=True)
        created_at: Mapped[str] = mapped_column(Text, nullable=False, index=True)
        message: Mapped[str] = mapped_column(Text, nullable=False)
        route: Mapped[str] = mapped_column(Text, nullable=False, index=True)
        route_reasoning: Mapped[str] = mapped_column(Text, nullable=False)
        final_answer: Mapped[str] = mapped_column(Text, nullable=False)
        warnings_json: Mapped[str] = mapped_column(Text, nullable=False)
        tool_calls_json: Mapped[str] = mapped_column(Text, nullable=False)
        selected_product_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
        conversation_context_json: Mapped[str] = mapped_column(Text, nullable=False)
        recommended_product_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
        parsed_intent_json: Mapped[str] = mapped_column(Text, nullable=False)
        faq_result_json: Mapped[str] = mapped_column(Text, nullable=False)
        compare_result_json: Mapped[str] = mapped_column(Text, nullable=False)
        providers_json: Mapped[str] = mapped_column(Text, nullable=False)
        provider: Mapped[str] = mapped_column(Text, nullable=False)
        model: Mapped[str] = mapped_column(Text, nullable=False)
        graph_runtime: Mapped[str] = mapped_column(Text, nullable=False)
