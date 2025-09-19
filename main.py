from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from contextlib import contextmanager

app = FastAPI(
    title="FastAPI REST API Örneği",
    description="Basit CRUD işlemleri için örnek API",
    version="1.0.0"
)

# Pydantic modelleri
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    name: Optional[str] = None
    price: Optional[float] = None

class Item(ItemBase):
    id: int

    class Config:
        from_attributes = True

# Veritabanı bağlantısı
DATABASE_URL = "items.db"

def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Uygulama başlatıldığında veritabanını initialize et
init_db()

@app.get("/")
async def root():
    return {"message": "FastAPI REST API Örneği"}

@app.get("/items/", response_model=List[Item])
async def get_items():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()
        return [dict(item) for item in items]

@app.post("/items/", response_model=Item)
async def create_item(item: ItemCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO items (name, description, price) VALUES (?, ?, ?)",
            (item.name, item.description, item.price)
        )
        conn.commit()
        item_id = cursor.lastrowid
        return Item(id=item_id, **item.dict())

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
