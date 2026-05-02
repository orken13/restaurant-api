from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, menu, orders

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Restaurant API")

# Allow requests from browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(orders.router)

@app.get("/")
def root():
    return {"message": "Restaurant API is running"}