from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import models, database 
import datetime
import json
import requests
from icalendar import Calendar
import google.generativeai as genai
import uvicorn
import os
import sys

# ==========================================
# [필수] API 키 입력
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# ==========================================

genai.configure(api_key=GOOGLE_API_KEY)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="나는 원장이다 Pro")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try: yield db
    finally: db.close()

# --- 스키마 ---
class ProductBase(BaseModel):
    name: str; unit_weight_g: float; stock_count: int; threshold_g: float
class ProductCreate(ProductBase): pass
class ProductResponse(ProductBase):
    id: int; total_weight_g: float
    class Config: from_attributes = True

# [수정] 매출 스키마 (사진 링크 추가)
class SaleCreate(BaseModel):
    date: str; amount: int; content: str; photo_link: Optional[str] = ""
class SaleResponse(SaleCreate):
    id: int
    class Config: from_attributes = True

class CustomerCreate(BaseModel):
    name: str; phone: str; memo: Optional[str] = ""; last_visit: str; next_visit: str
class CustomerResponse(CustomerCreate):
    id: int
    class Config: from_attributes = True

class RecipeRequest(BaseModel):
    procedure_type: str; hair_length: str; hair_condition: str; target_color: str
class CalendarRequest(BaseModel):
    ical_url: str

# [NEW] 스타일 추천 요청 스키마
class StyleRequest(BaseModel):
    face_shape: str     # 얼굴형 (계란형, 둥근형 등)
    current_trend: str  # 트렌드 (내추럴, 힙합, K-POP 등)
    gender: str         # 성별

# --- API 구현 ---

# 1. 재고
@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    total = product.unit_weight_g * product.stock_count
    item = models.Product(name=product.name, unit_weight_g=product.unit_weight_g, stock_count=product.stock_count, total_weight_g=total, threshold_g=product.threshold_g)
    db.add(item); db.commit(); db.refresh(item)
    return item
@app.get("/products", response_model=List[ProductResponse])
def read_products(db: Session = Depends(get_db)): return db.query(models.Product).all()
@app.delete("/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Product).filter(models.Product.id == id).first()
    if item: db.delete(item); db.commit()
    return {"msg": "삭제됨"}

# 2. 매출 (사진 링크 포함)
@app.post("/sales", response_model=SaleResponse)
def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    item = models.Sale(date=sale.date, amount=sale.amount, content=sale.content, photo_link=sale.photo_link)
    db.add(item); db.commit(); db.refresh(item)
    return item
@app.get("/sales", response_model=List[SaleResponse])
def read_sales(db: Session = Depends(get_db)):
    return db.query(models.Sale).order_by(models.Sale.date.desc(), models.Sale.id.desc()).all()
@app.delete("/sales/{id}")
def delete_sale(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Sale).filter(models.Sale.id == id).first()
    if item: db.delete(item); db.commit()
    return {"msg": "삭제됨"}

# 3. 손님
@app.post("/customers", response_model=CustomerResponse)
def create_customer(c: CustomerCreate, db: Session = Depends(get_db)):
    item = models.Customer(name=c.name, phone=c.phone, memo=c.memo, last_visit=c.last_visit, next_visit=c.next_visit)
    db.add(item); db.commit(); db.refresh(item)
    return item
@app.get("/customers", response_model=List[CustomerResponse])
def read_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).order_by(models.Customer.next_visit.asc()).all()
@app.delete("/customers/{id}")
def delete_customer(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Customer).filter(models.Customer.id == id).first()
    if item: db.delete(item); db.commit()
    return {"msg": "삭제됨"}

# 4. AI (염색약 계산)
@app.post("/procedure/calculate_ai")
def calculate_ai_recipe(req: RecipeRequest):
    prompt = f"""Role: Expert Hair Designer. Input: {req.procedure_type}, {req.target_color}, {req.hair_length}, {req.hair_condition}. Knowledge: Gray/White hair needs coverage. Output JSON: "dye_g", "oxidizer_g", "oxidizer_percent", "mix_ratio", "ph_tip", "comment". Language: Korean."""
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        res = model.generate_content(prompt)
        return json.loads(res.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        return {"dye_g": 0, "oxidizer_g": 0, "oxidizer_percent": 0, "mix_ratio": "-", "ph_tip": "AI 에러", "comment": str(e)}

# 5. [NEW] AI (스타일 추천)
@app.post("/procedure/recommend_style")
def recommend_style(req: StyleRequest):
    prompt = f"""
    Role: Trendy Hair Stylist in 2026.
    Customer: {req.gender}, Face Shape: {req.face_shape}, Preferred Vibe: {req.current_trend}.
    Task: Recommend 3 specific hairstyles.
    Output Format: JSON Only. Key: "recommendations" (Array of strings, e.g., ["Style 1", "Style 2", "Style 3"]).
    Language: Korean.
    """
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        res = model.generate_content(prompt)
        return json.loads(res.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        return {"recommendations": ["AI 연결 실패: 다시 시도해주세요."]}

@app.post("/reservations/naver")
def get_naver_calendar(req: CalendarRequest):
    if not req.ical_url: return []
    try:
        res = requests.get(req.ical_url); res.encoding = 'utf-8'
        cal = Calendar.from_ical(res.text)
        events = []
        for c in cal.walk():
            if c.name == "VEVENT":
                start = c.get('dtstart').dt
                events.append({"title": str(c.get('summary')), "start": start.isoformat() if hasattr(start, 'isoformat') else str(start), "color": "#03C75A"})
        return events
    except: return []

if __name__ == "__main__":
    print("✂️ 미용실 관리 시스템 가동 중...")
    uvicorn.run(app, host="0.0.0.0", port=8000)