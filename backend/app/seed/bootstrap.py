from app.catalog.data import PRODUCT_CATALOG
from app.faq.data import FAQ_ENTRIES
from app.schemas.faq import FaqEntry
from app.schemas.products import ProductSummary


def load_seed_products() -> list[ProductSummary]:
    return [product.model_copy(deep=True) for product in PRODUCT_CATALOG]


def load_seed_faq_entries() -> list[FaqEntry]:
    return [entry.model_copy(deep=True) for entry in FAQ_ENTRIES]
