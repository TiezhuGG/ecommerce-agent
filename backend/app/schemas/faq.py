from pydantic import BaseModel, Field


class FaqEntry(BaseModel):
    """Searchable knowledge-base entry."""

    id: str = Field(..., description="Knowledge entry ID")
    topic: str = Field(..., description="Knowledge topic")
    question: str = Field(..., description="Canonical question title")
    answer: str = Field(..., description="Canonical short answer")
    source_label: str = Field(..., description="Source label")
    question_aliases: list[str] = Field(default_factory=list, description="Alternative question phrasings")
    keywords: list[str] = Field(default_factory=list, description="Search keywords")
    body: str = Field(default="", description="Extended knowledge body")


class FaqCitation(BaseModel):
    """Matched citation snippet."""

    entry_id: str = Field(..., description="Matched entry ID")
    title: str = Field(..., description="Matched entry title")
    snippet: str = Field(..., description="Matched snippet")
    source_label: str = Field(..., description="Snippet source label")
    score: float = Field(..., description="Retrieval score")


class FaqMatchSignal(BaseModel):
    """Why a FAQ entry matched the user question."""

    kind: str = Field(..., description="Match factor kind")
    label: str = Field(..., description="Human-readable label")
    matched_value: str = Field(..., description="Matched value from the knowledge base")
    detail: str = Field(default="", description="Additional explanation detail")


class FaqAskRequest(BaseModel):
    """Knowledge-base ask request."""

    question: str = Field(..., min_length=1, description="User question")


class FaqAskResponse(BaseModel):
    """Knowledge-base ask response."""

    question: str
    answer: str
    matched_entry: FaqEntry | None
    source_label: str
    suggestions: list[str]
    citations: list[FaqCitation] = Field(default_factory=list)
    match_signals: list[FaqMatchSignal] = Field(default_factory=list)
    retrieval_mode: str = Field(default="knowledge-rag-v1")
    retrieval_provider: str = Field(default="knowledge-rag-v1-local-retrieval")
    answer_provider: str = Field(default="")


class FaqEntryListResponse(BaseModel):
    """Knowledge-base admin list response."""

    backend: str
    items: list[FaqEntry] = Field(default_factory=list)


class FaqEntryUpsertRequest(BaseModel):
    """Create or update knowledge entry payload."""

    topic: str = Field(..., min_length=1, description="Knowledge topic")
    question: str = Field(..., min_length=1, description="Canonical question title")
    answer: str = Field(..., min_length=1, description="Canonical short answer")
    source_label: str = Field(..., min_length=1, description="Source label")
    question_aliases: list[str] = Field(default_factory=list, description="Alternative question phrasings")
    keywords: list[str] = Field(default_factory=list, description="Search keywords")
    body: str = Field(default="", description="Extended knowledge body")


class FaqDeleteResponse(BaseModel):
    """Knowledge-base delete response."""

    deleted: bool = True
    entry_id: str


class FaqEntryImportItem(BaseModel):
    """Knowledge entry payload used by bulk import."""

    id: str | None = Field(default=None, description="Knowledge entry ID, optional")
    topic: str = Field(..., min_length=1, description="Knowledge topic")
    question: str = Field(..., min_length=1, description="Canonical question title")
    answer: str = Field(..., min_length=1, description="Canonical short answer")
    source_label: str = Field(..., min_length=1, description="Source label")
    question_aliases: list[str] = Field(default_factory=list, description="Alternative question phrasings")
    keywords: list[str] = Field(default_factory=list, description="Search keywords")
    body: str = Field(default="", description="Extended knowledge body")


class FaqEntryImportRequest(BaseModel):
    """Knowledge-base bulk import request."""

    mode: str = Field(default="upsert", description="Supported values: upsert, replace")
    items: list[FaqEntryImportItem] = Field(default_factory=list, description="Entries to import")


class FaqEntryImportResponse(BaseModel):
    """Knowledge-base bulk import result."""

    mode: str
    imported_count: int
    created_count: int
    updated_count: int
    backend: str
