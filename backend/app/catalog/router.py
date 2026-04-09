from fastapi import APIRouter, HTTPException, Query

from app.catalog.service import (
    ProductAdminUnavailableError,
    ProductNotFoundError,
    create_product,
    delete_product,
    list_products_admin,
    search_products,
    update_product,
)
from app.schemas.products import (
    ProductDeleteResponse,
    ProductListResponse,
    ProductSearchResponse,
    ProductSummary,
    ProductUpsertRequest,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductSearchResponse)
async def get_products(
    keyword: str = Query(default="", description="商品搜索关键词"),
    category: str = Query(default="", description="精确分类筛选"),
    brand: str = Query(default="", description="精确品牌筛选"),
    max_price: int | None = Query(default=None, ge=0, description="人民币预算上限"),
) -> ProductSearchResponse:
    """Product search endpoint."""

    return search_products(
        keyword=keyword,
        category=category,
        brand=brand,
        max_price=max_price,
    )


@router.get("/admin", response_model=ProductListResponse)
async def list_products_admin_endpoint() -> ProductListResponse:
    """Product admin list endpoint."""

    try:
        return list_products_admin()
    except ProductAdminUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/admin", response_model=ProductSummary)
async def create_product_endpoint(payload: ProductUpsertRequest) -> ProductSummary:
    """Product create endpoint."""

    try:
        return create_product(payload)
    except ProductAdminUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.put("/admin/{product_id}", response_model=ProductSummary)
async def update_product_endpoint(product_id: str, payload: ProductUpsertRequest) -> ProductSummary:
    """Product update endpoint."""

    try:
        return update_product(product_id, payload)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProductAdminUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.delete("/admin/{product_id}", response_model=ProductDeleteResponse)
async def delete_product_endpoint(product_id: str) -> ProductDeleteResponse:
    """Product delete endpoint."""

    try:
        return delete_product(product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProductAdminUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
