from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud.utils import commit_or_conflict
from app.exceptions import ConflictError, NotFoundError
from app.models import Category, Product
from app.schemas import CategoryCreate, CategoryUpdate


def get_categories(db: Session, skip: int, limit: int) -> List[Category]:
    stmt = select(Category).order_by(Category.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError(f"Category with id {category_id} not found")
    return category


def find_by_name(db: Session, name: str) -> Optional[Category]:
    return db.scalars(select(Category).where(Category.name == name)).first()


def create_category(db: Session, data: CategoryCreate) -> Category:
    if find_by_name(db, data.name):
        raise ConflictError(f"Category with name '{data.name}' already exists")
    category = Category(**data.model_dump())
    db.add(category)
    commit_or_conflict(db, f"Category with name '{data.name}' already exists")
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    changes = data.model_dump(exclude_unset=True)
    new_name = changes.get("name")
    if new_name is not None:
        existing = find_by_name(db, new_name)
        if existing and existing.id != category.id:
            raise ConflictError(f"Category with name '{new_name}' already exists")
    for field, value in changes.items():
        setattr(category, field, value)
    commit_or_conflict(db, "Category name already exists")
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    product_count = db.scalar(
        select(func.count(Product.id)).where(Product.category_id == category_id)
    )
    if product_count:
        raise ConflictError(
            f"Cannot delete category {category_id}: it still has {product_count} product(s)"
        )
    db.delete(category)
    commit_or_conflict(db, f"Cannot delete category {category_id}: it is still in use")
