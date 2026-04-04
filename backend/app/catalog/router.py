from fastapi import APIRouter, Query

from app.catalog.service import search_products
from app.schemas.products import ProductSearchResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductSearchResponse)
async def get_products(
    keyword: str = Query(default="", description="Free-text keyword used for the demo search."),
    category: str = Query(default="", description="Exact category filter."),
    brand: str = Query(default="", description="Exact brand filter."),
    max_price: int | None = Query(default=None, ge=0, description="Upper budget limit in CNY."),
) -> ProductSearchResponse:
    """Expose the catalog search capability to the frontend.

    The frontend search panel maps directly to these query parameters.
    Keeping this as a small, explicit HTTP contract makes it easy to teach:
    first the UI learns to talk to a normal backend endpoint, then the agent
    layer will learn to call the same capability as a structured tool.
    """

    return search_products(
        keyword=keyword,
        category=category,
        brand=brand,
        max_price=max_price,
    )
