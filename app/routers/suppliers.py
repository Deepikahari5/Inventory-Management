from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.crud import supplier as crud
from app.database import get_db
from app.schemas import (
    MessageResponse,
    ProductResponse,
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db)):
    return crud.create_supplier(db, data)


@router.get("", response_model=List[SupplierResponse])
def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return crud.get_suppliers(db, skip, limit)


@router.get("/{supplier_id}/products", response_model=List[ProductResponse])
def list_supplier_products(
    supplier_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return crud.get_supplier_products(db, supplier_id, skip, limit)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    return crud.get_supplier(db, supplier_id)


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int, data: SupplierUpdate, db: Session = Depends(get_db)
):
    return crud.update_supplier(db, supplier_id, data)


@router.delete("/{supplier_id}", response_model=MessageResponse)
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    crud.delete_supplier(db, supplier_id)
    return MessageResponse(message=f"Supplier {supplier_id} deleted successfully")
