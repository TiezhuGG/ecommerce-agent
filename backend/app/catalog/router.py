from fastapi import APIRouter, Query

from app.catalog.service import search_products
from app.schemas.products import ProductSearchResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductSearchResponse)
async def get_products(
    keyword: str = Query(default="", description="商品搜索关键词。"),
    category: str = Query(default="", description="精确的商品分类筛选。"),
    brand: str = Query(default="", description="精确的品牌筛选。"),
    max_price: int | None = Query(default=None, ge=0, description="人民币预算上限。"),
) -> ProductSearchResponse:
    """商品搜索工具接口。"""

    return search_products(
        keyword=keyword,
        category=category,
        brand=brand,
        max_price=max_price,
    )
