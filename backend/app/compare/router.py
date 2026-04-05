from fastapi import APIRouter, HTTPException

from app.compare.service import compare_products
from app.schemas.compare import CompareRequest, CompareResponse

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
async def compare_products_endpoint(payload: CompareRequest) -> CompareResponse:
    """商品对比工具接口。"""

    try:
        return compare_products(payload.product_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
