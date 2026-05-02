# Restaurant Order System

A production-ready microservice architecture for restaurant order tracking — built with FastAPI, PostgreSQL, Redis, RabbitMQ, and Docker Compose.

---

## Architecture

```
Browser (Nginx UI)
       │
       ▼
  FastAPI Service          ← REST API + JWT Auth
   │       │    │
   ▼       ▼    ▼
Postgres Redis  RabbitMQ
               │       │
               ▼       ▼
          Kitchen   Notification
          Service    Service
```

### Services

| Service | Role |
|---------|------|
| **FastAPI** | REST endpoints, JWT authentication, business logic |
| **PostgreSQL** | Permanent storage — users, orders, menu items |
| **Redis** | Active order cache (TTL = 2 hours) |
| **RabbitMQ** | Message queue between services |
| **Kitchen Service** | Listens to `orders` queue, displays new orders |
| **Notification Service** | Listens to `notifications` queue, sends status updates |
| **Nginx** | Serves the frontend UI |

---

## Order Flow

```
1. Customer places order → POST /orders
        ↓
2. FastAPI:
   → Writes to PostgreSQL (permanent)
   → Writes to Redis (active, TTL=2h)
   → Publishes to RabbitMQ "orders" queue

3. Kitchen Service receives from RabbitMQ
   → Prints: NEW ORDER — Table 5 (Order #2)

4. Kitchen updates status → PATCH /orders/{id}/status
        ↓
5. FastAPI:
   → Updates PostgreSQL
   → Updates Redis
   → Publishes to RabbitMQ "notifications" queue

6. Notification Service receives from RabbitMQ
   → Prints: Siparişiniz hazırlanıyor...

7. Kitchen marks READY → Redis entry deleted, PostgreSQL record stays
```

---

## Tech Stack

```
FastAPI        → Python web framework, auto-generates /docs
SQLAlchemy     → ORM (Python ↔ PostgreSQL)
Alembic        → Database migrations
JWT + bcrypt   → Authentication & password hashing
Redis          → Active order cache
RabbitMQ       → Async messaging between microservices
Docker Compose → Orchestrates all services
Nginx          → Serves frontend UI
```

---

## Project Structure

```
restaurant-api/
├── docker-compose.yml
├── ui/
│   └── index.html          # Frontend (Menu, Kitchen screen, Login)
└── services/
    ├── api/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app/
    │       ├── main.py         # FastAPI app + CORS
    │       ├── database.py     # PostgreSQL connection + session
    │       ├── models.py       # SQLAlchemy models (User, Order, MenuItem)
    │       ├── schemas.py      # Pydantic request/response schemas
    │       ├── auth.py         # JWT + bcrypt
    │       └── routers/
    │           ├── auth.py     # /auth/register, /auth/login
    │           ├── menu.py     # /menu/
    │           └── orders.py   # /orders/ + Redis + RabbitMQ
    ├── kitchen/
    │   ├── Dockerfile
    │   └── main.py             # Consumes "orders" queue
    └── notification/
        ├── Dockerfile
        └── main.py             # Consumes "notifications" queue
```

---

## Setup & Run

```bash
# Clone the repo
git clone https://github.com/orken13/restaurant-api.git
cd restaurant-api

# Start all services
docker compose up --build
```

| Service | URL |
|---------|-----|
| UI | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| RabbitMQ Dashboard | http://localhost:15672 (guest/guest) |

---

## API Endpoints

### Auth
```
POST /auth/register   → Create account (cashier or kitchen role)
POST /auth/login      → Login, get JWT token
```

### Menu (cashier JWT required for write)
```
GET    /menu/         → List all menu items (public)
POST   /menu/         → Add menu item (cashier only)
DELETE /menu/{id}     → Remove menu item (cashier only)
```

### Orders
```
POST   /orders/               → Place order (anonymous)
GET    /orders/{id}           → Get order details
GET    /orders/active         → Get active orders from Redis
PATCH  /orders/{id}/status    → Update status (kitchen JWT required)
```

---

## Roles

| Role | Can Do |
|------|--------|
| **Anonymous** (customer) | Browse menu, place orders |
| **Cashier** | Login, manage menu items |
| **Kitchen** | Login, update order status |

---

## Database Migrations (Alembic)

```bash
# Create migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Roll back
alembic downgrade -1
```