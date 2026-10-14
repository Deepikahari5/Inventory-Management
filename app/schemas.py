import re
from datetime import datetime
from decimal import Decimal
from typing import ClassVar, Optional, Set

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\s\-()]{5,18}[0-9]$")


class StrictBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class PartialUpdateBase(StrictBase):
    NULLABLE_FIELDS: ClassVar[Set[str]] = set()

    @model_validator(mode="after")
    def validate_partial_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        for field_name in self.model_fields_set:
            if field_name in self.NULLABLE_FIELDS:
                continue
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


def _validate_phone(value: str) -> str:
    if not PHONE_PATTERN.match(value):
        raise ValueError("Invalid phone number format")
    return value


class CategoryCreate(StrictBase):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)


class CategoryUpdate(PartialUpdateBase):
    NULLABLE_FIELDS: ClassVar[Set[str]] = {"description"}

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    created_at: datetime


class SupplierCreate(StrictBase):
    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    phone_number: str = Field(..., min_length=7, max_length=20)
    address: Optional[str] = Field(None, max_length=2000)
    company_name: str = Field(..., min_length=1, max_length=150)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, value: str) -> str:
        return _validate_phone(value)


class SupplierUpdate(PartialUpdateBase):
    NULLABLE_FIELDS: ClassVar[Set[str]] = {"address"}

    name: Optional[str] = Field(None, min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=7, max_length=20)
    address: Optional[str] = Field(None, max_length=2000)
    company_name: Optional[str] = Field(None, min_length=1, max_length=150)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: Optional[str]) -> Optional[str]:
        return value.lower() if value else value

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, value: Optional[str]) -> Optional[str]:
        return _validate_phone(value) if value else value


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone_number: str
    address: Optional[str]
    company_name: str
    created_at: datetime


class ProductCreate(StrictBase):
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=2000)
    category_id: int = Field(..., gt=0)
    supplier_id: int = Field(..., gt=0)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    quantity: int = Field(..., ge=0)


class ProductUpdate(PartialUpdateBase):
    NULLABLE_FIELDS: ClassVar[Set[str]] = {"description"}

    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=2000)
    category_id: Optional[int] = Field(None, gt=0)
    supplier_id: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    quantity: Optional[int] = Field(None, ge=0)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    category_id: int
    supplier_id: int
    price: float
    quantity: int
    created_at: datetime
    updated_at: datetime


class InventoryValueResponse(BaseModel):
    total_products: int
    total_quantity: int
    total_inventory_value: float


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    database: str
