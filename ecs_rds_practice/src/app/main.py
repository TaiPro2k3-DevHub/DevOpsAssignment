from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db, init_db, DB_HOST, DB_NAME, DB_PORT
from app import models, schemas

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo kết nối DB và tạo bảng tự động
    init_db()
    yield

app = FastAPI(
    title="ECS RDS PostgreSQL Practice API",
    description="FastAPI service deployed on AWS ECS connecting to AWS RDS PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", response_class=HTMLResponse)
def index(db: Session = Depends(get_db)):
    db_status = "Disconnected"
    item_count = 0
    try:
        db.execute(text("SELECT 1"))
        db_status = "Connected successfully!"
        item_count = db.query(models.Item).count()
    except Exception as e:
        db_status = f"Error: {str(e)}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AWS ECS + RDS PostgreSQL Demo</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #0f172a, #1e293b);
                color: #f8fafc;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
                padding: 20px;
            }}
            .card {{
                background: rgba(30, 41, 59, 0.8);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 32px;
                max-width: 600px;
                width: 100%;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
            }}
            h1 {{
                margin-top: 0;
                font-size: 24px;
                color: #38bdf8;
            }}
            .badge {{
                display: inline-block;
                padding: 6px 14px;
                border-radius: 9999px;
                font-size: 14px;
                font-weight: 600;
                background-color: {"#10b981" if "Connected" in db_status else "#ef4444"};
                color: white;
            }}
            .info-box {{
                background: #0f172a;
                border-radius: 8px;
                padding: 16px;
                margin: 20px 0;
                font-family: monospace;
                font-size: 14px;
                line-height: 1.6;
            }}
            .links a {{
                color: #38bdf8;
                text-decoration: none;
                font-weight: 600;
                margin-right: 16px;
            }}
            .links a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>AWS ECS & RDS PostgreSQL Practice</h1>
            <p>Trạng thái kết nối Database: <span class="badge">{db_status}</span></p>
            <div class="info-box">
                <strong>Host:</strong> {DB_HOST}<br>
                <strong>Port:</strong> {DB_PORT}<br>
                <strong>Database:</strong> {DB_NAME}<br>
                <strong>Số lượng items hiện tại:</strong> {item_count}
            </div>
            <div class="links">
                <a href="/docs" target="_blank">Swagger API Docs &rarr;</a>
                <a href="/items" target="_blank">Xem danh sách Items (JSON) &rarr;</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected", "host": DB_HOST}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database unreachable: {str(e)}")

@app.get("/items", response_model=List[schemas.ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return db.query(models.Item).order_by(models.Item.id.desc()).all()

@app.post("/items", response_model=schemas.ItemResponse, status_code=201)
def create_item(item_in: schemas.ItemCreate, db: Session = Depends(get_db)):
    new_item = models.Item(
        title=item_in.title,
        description=item_in.description
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item
