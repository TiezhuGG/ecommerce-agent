from pydantic import BaseModel, Field


class ProductSummary(BaseModel):
    """Represents one product card shown in the frontend result list."""

    id: str = Field(..., description="Stable product id used by the compare and detail modules later.")
    name: str = Field(..., description="Real-world product model shown to the user.")
    category: str = Field(..., description="Business category used for filtering.")
    brand: str = Field(..., description="Brand name used in filters and product cards.")
    price: int = Field(..., description="Demo reference price in CNY for search and compare scenarios.")
    price_note: str = Field(..., description="Clarifies that price is a non-real-time demo reference.")
    summary: str = Field(..., description="Short selling-point summary displayed in the card.")
    scenario: str = Field(..., description="Typical usage scenario for the product.")
    tags: list[str] = Field(default_factory=list, description="Short feature tags used for display and keyword matching.")
    specs: list[str] = Field(default_factory=list, description="Core specs displayed in the result card.")
    official_url: str = Field(..., description="Official product page for realism and future traceability.")


class ProductSearchResponse(BaseModel):
    """The frontend needs both the matched items and the metadata for filter widgets."""

    items: list[ProductSummary]
    total: int
    applied_filters: list[str]
    available_categories: list[str]
    available_brands: list[str]
