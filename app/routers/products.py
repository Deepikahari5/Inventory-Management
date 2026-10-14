from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.crud import product as crud
from app.database import get_db
from app.schemas import (
    InventoryValueResponse,
    MessageResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, data)


@router.get("", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = Query(None, min_length=1, max_length=150),
    category_id: Optional[int] = Query(None, gt=0),
    supplier_id: Optional[int] = Query(None, gt=0),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return crud.get_products(
        db, search, category_id, supplier_id, min_price, max_price, skip, limit
    )


@router.get("/inventory-value", response_model=InventoryValueResponse)
def inventory_value(db: Session = Depends(get_db)):
    return crud.get_inventory_value(db)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return crud.get_product(db, product_id)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    return crud.update_product(db, product_id, data)


@router.delete("/{product_id}", response_model=MessageResponse)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    crud.delete_product(db, product_id)
    return MessageResponse(message=f"Product {product_id} deleted successfully")
