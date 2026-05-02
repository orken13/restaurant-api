from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, OrderStatus

# ── Auth ─────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True

# ── Menu ─────────────────────────────────────────

class MenuItemCreate(BaseModel):
    name: str
    price: float
    category: str

class MenuItemResponse(BaseModel):
    id: int
    name: str
    price: float
    category: str
    available: int

    class Config:
        from_attributes = True

# ── Orders ───────────────────────────────────────

class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int

class OrderCreate(BaseModel):
    table_number: int
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    quantity: int
    price: float

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    table_number: int
    status: OrderStatus
    total: float
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: OrderStatus