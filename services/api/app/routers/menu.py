from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MenuItem, UserRole
from app.schemas import MenuItemCreate, MenuItemResponse
from app.auth import require_role

router = APIRouter(prefix="/menu", tags=["menu"])

@router.get("/", response_model=list[MenuItemResponse])
def get_menu(db: Session = Depends(get_db)):
    # Public endpoint — no auth required
    return db.query(MenuItem).filter(MenuItem.available == 1).all()

@router.post("/", response_model=MenuItemResponse, status_code=201)
def create_menu_item(
    data: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.cashier))
):
    # Only cashier can add menu items
    item = MenuItem(name=data.name, price=data.price, category=data.category)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.cashier))
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    db.delete(item)
    db.commit()
    return {"message": f"Menu item {item_id} deleted"}