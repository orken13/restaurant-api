import json
import redis
import aio_pika
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, OrderItem, MenuItem, OrderStatus, UserRole
from app.schemas import OrderCreate, OrderResponse, StatusUpdate
from app.auth import get_current_user, require_role

router = APIRouter(prefix="/orders", tags=["orders"])

# Redis connection
r = redis.Redis(host="redis", port=6379, decode_responses=True)

async def publish_to_rabbitmq(queue: str, message: dict):
    # Publish message to RabbitMQ queue
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(queue, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=queue
        )

@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    # Calculate total price
    total = 0.0
    order_items = []

    for item_data in data.items:
        menu_item = db.query(MenuItem).filter(MenuItem.id == item_data.menu_item_id).first()
        if not menu_item:
            raise HTTPException(status_code=404, detail=f"Menu item {item_data.menu_item_id} not found")
        total += menu_item.price * item_data.quantity
        order_items.append((menu_item, item_data.quantity))

    # Save order to PostgreSQL
    order = Order(table_number=data.table_number, total=total)
    db.add(order)
    db.flush()

    for menu_item, quantity in order_items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            quantity=quantity,
            price=menu_item.price
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    # Save to Redis as active order (TTL = 2 hours)
    r.setex(
        f"order:{order.id}",
        7200,
        json.dumps({"id": order.id, "table": order.table_number, "status": "pending", "total": total})
    )

    # Publish to RabbitMQ → kitchen will receive this
    await publish_to_rabbitmq("orders", {
        "order_id": order.id,
        "table_number": order.table_number,
        "status": "pending",
        "items": [{"name": mi.name, "quantity": q} for mi, q in order_items]
    })

    return order

@router.get("/active")
def get_active_orders():
    # Return all active orders from Redis
    keys = r.keys("order:*")
    orders = [json.loads(r.get(k)) for k in keys]
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.patch("/{order_id}/status")
async def update_status(
    order_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.kitchen))
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update status in PostgreSQL
    order.status = data.status
    db.commit()

    if data.status == OrderStatus.ready:
        # Remove from Redis — no longer active
        r.delete(f"order:{order_id}")
    else:
        # Update status in Redis
        cached = r.get(f"order:{order_id}")
        if cached:
            order_data = json.loads(cached)
            order_data["status"] = data.status
            r.setex(f"order:{order_id}", 7200, json.dumps(order_data))

    # Notify via RabbitMQ → notification service will send to customer
    await publish_to_rabbitmq("notifications", {
        "order_id": order_id,
        "status": data.status,
        "table_number": order.table_number
    })

    return {"message": f"Order {order_id} status updated to {data.status}"}