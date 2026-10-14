from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud.utils import commit_or_conflict
from app.exceptions import BadRequestError, NotFoundError
from app.models import Category, Product, Supplier
from app.schemas import InventoryValueResponse, ProductCreate, ProductUpdate


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _ensure_category_exists(db: Session, category_id: int) -> None:
    if db.get(Category, category_id) is None:
        raise NotFoundError(f"Category with id {category_id} not found")


def _ensure_supplier_exists(db: Session, supplier_id: int) -> None:
    if db.get(Supplier, supplier_id) is None:
        raise NotFoundError(f"Supplier with id {supplier_id} not found")


def get_products(
    db: Session,
    search: Optional[str],
    category_id: Optional[int],
    supplier_id: Optional[int],
    min_price: Optional[Decimal],
    max_price: Optional[Decimal],
    skip: int,
    limit: int,
) -> List[Product]:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise BadRequestError("min_price cannot be greater than max_price")

    stmt = select(Product)
    if search:
        pattern = f"%{_escape_like(search.strip())}%"
        stmt = stmt.where(Product.name.ilike(pattern, escape="\\"))
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if supplier_id is not None:
        stmt = stmt.where(Product.supplier_id == supplier_id)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)

    stmt = stmt.order_by(Product.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise NotFoundError(f"Product with id {product_id} not found")
    return product


def create_product(db: Session, data: ProductCreate) -> Product:
    _ensure_category_exists(db, data.category_id)
    _ensure_supplier_exists(db, data.supplier_id)
    product = Product(**data.model_dump())
    db.add(product)
    commit_or_conflict(db, "Invalid category or supplier reference")
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("category_id") is not None:
        _ensure_category_exists(db, changes["category_id"])
    if changes.get("supplier_id") is not None:
        _ensure_supplier_exists(db, changes["supplier_id"])
    for field, value in changes.items():
        setattr(product, field, value)
    commit_or_conflict(db, "Invalid category or supplier reference")
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    db.delete(product)
    commit_or_conflict(db, f"Cannot delete product {product_id}")


def get_inventory_value(db: Session) -> InventoryValueResponse:
    row = db.execute(
        select(
            func.count(Product.id),
            func.coalesce(func.sum(Product.quantity), 0),
            func.coalesce(func.sum(Product.price * Product.quantity), 0),
        )
    ).one()
    return InventoryValueResponse(
        total_products=int(row[0]),
        total_quantity=int(row[1]),
        total_inventory_value=round(float(row[2]), 2),
    )
