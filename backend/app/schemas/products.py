from pydantic import BaseModel, Field


class ProductSummary(BaseModel):
    """Canonical product model shared across search, compare, FAQ, and agent flows."""

    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    brand: str = Field(..., description="Brand name")
    price: int = Field(..., description="Display price in CNY")
    price_note: str = Field(..., description="Price note")
    summary: str = Field(..., description="Short selling-point summary")
    scenario: str = Field(..., description="Recommended usage scenario")
    tags: list[str] = Field(default_factory=list, description="Display and search tags")
    specs: list[str] = Field(default_factory=list, description="Core spec bullets")
    official_url: str = Field(..., description="Official product page URL")


class ProductSearchResponse(BaseModel):
    """Product search response."""

    items: list[ProductSummary]
    total: int
    applied_filters: list[str]
    available_categories: list[str]
    available_brands: list[str]


class ProductListResponse(BaseModel):
    """Product admin list response."""

    backend: str
    items: list[ProductSummary] = Field(default_factory=list)


class ProductUpsertRequest(BaseModel):
    """Create or update product payload."""

    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    price: int = Field(..., ge=0)
    price_note: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    scenario: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    specs: list[str] = Field(default_factory=list)
    official_url: str = Field(..., min_length=1)


class ProductDeleteResponse(BaseModel):
    """Product delete response."""

    deleted: bool = True
    product_id: str
