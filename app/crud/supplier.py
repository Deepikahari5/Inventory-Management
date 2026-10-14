from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud.utils import commit_or_conflict
from app.exceptions import ConflictError, NotFoundError
from app.models import Product, Supplier
from app.schemas import SupplierCreate, SupplierUpdate


def get_suppliers(db: Session, skip: int, limit: int) -> List[Supplier]:
    stmt = select(Supplier).order_by(Supplier.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_supplier(db: Session, supplier_id: int) -> Supplier:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise NotFoundError(f"Supplier with id {supplier_id} not found")
    return supplier


def find_by_email(db: Session, email: str) -> Optional[Supplier]:
    return db.scalars(select(Supplier).where(Supplier.email == email)).first()


def create_supplier(db: Session, data: SupplierCreate) -> Supplier:
    if find_by_email(db, data.email):
        raise ConflictError(f"Supplier with email '{data.email}' already exists")
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    commit_or_conflict(db, f"Supplier with email '{data.email}' already exists")
    db.refresh(supplier)
    return supplier


def update_supplier(db: Session, supplier_id: int, data: SupplierUpdate) -> Supplier:
    supplier = get_supplier(db, supplier_id)
    changes = data.model_dump(exclude_unset=True)
    new_email = changes.get("email")
    if new_email is not None:
        existing = find_by_email(db, new_email)
        if existing and existing.id != supplier.id:
            raise ConflictError(f"Supplier with email '{new_email}' already exists")
    for field, value in changes.items():
        setattr(supplier, field, value)
    commit_or_conflict(db, "Supplier email already exists")
    db.refresh(supplier)
    return supplier


def delete_supplier(db: Session, supplier_id: int) -> None:
    supplier = get_supplier(db, supplier_id)
    product_count = db.scalar(
        select(func.count(Product.id)).where(Product.supplier_id == supplier_id)
    )
    if product_count:
        raise ConflictError(
            f"Cannot delete supplier {supplier_id}: it still supplies {product_count} product(s)"
        )
    db.delete(supplier)
    commit_or_conflict(db, f"Cannot delete supplier {supplier_id}: it is still in use")


def get_supplier_products(
    db: Session, supplier_id: int, skip: int, limit: int
) -> List[Product]:
    get_supplier(db, supplier_id)
    stmt = (
        select(Product)
        .where(Product.supplier_id == supplier_id)
        .order_by(Product.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
