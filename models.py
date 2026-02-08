from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# 1. 재고
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    unit_weight_g = Column(Float)
    stock_count = Column(Integer, default=0)
    total_weight_g = Column(Float, default=0.0)
    threshold_g = Column(Float, default=100.0)
    usage_logs = relationship("UsageLog", back_populates="product")

# 2. [수정] 매출 장부 (사진 링크 추가)
class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)
    amount = Column(Integer)
    content = Column(String)
    photo_link = Column(String, nullable=True) # [NEW] 사진 주소 저장

# 3. 손님 관리
class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    memo = Column(String, nullable=True)
    last_visit = Column(String)
    next_visit = Column(String)

# 4. 처방 규칙 (확장용)
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    procedure_name = Column(String)
    hair_condition = Column(String)
    base_oxidizer_percent = Column(Float)
    base_amount_g = Column(Float)

# 5. 사용 기록
class UsageLog(Base):
    __tablename__ = "usage_logs"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    used_amount_g = Column(Float)
    customer_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    product = relationship("Product", back_populates="usage_logs")

# 6. 예약
class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(String, primary_key=True)
    customer_name = Column(String)
    procedure_name = Column(String)
    expected_price = Column(Integer)
    status = Column(String)
    date = Column(DateTime)