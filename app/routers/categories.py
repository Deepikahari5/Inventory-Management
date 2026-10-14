from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.crud import category as crud
from app.database import get_db
from app.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    MessageResponse,
)

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db, data)


@router.get("", response_model=List[CategoryResponse])
def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return crud.get_categories(db, skip, limit)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    return crud.get_category(db, category_id)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)
):
    return crud.update_category(db, category_id, data)


@router.delete("/{category_id}", response_model=MessageResponse)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    crud.delete_category(db, category_id)
    return MessageResponse(message=f"Category {category_id} deleted successfully")
