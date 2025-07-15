#!/usr/bin/env python3
"""
PowerAutomation 積分系統後端服務
支持500人同時在線，完整的充值積分系統
"""

import os
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import redis.asyncio as redis
import jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import bcrypt
import stripe
import logging
from decimal import Decimal
import json

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/powerautomation")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")

# Stripe 配置
stripe.api_key = STRIPE_SECRET_KEY

# 數據庫設置
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# JWT 安全
security = HTTPBearer()

# 數據模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    credits = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 關聯關係
    orders = relationship("Order", back_populates="user")
    credit_transactions = relationship("CreditTransaction", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_number = Column(String, unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="CNY")
    credits = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending, paid, failed, refunded
    payment_method = Column(String)  # stripe, alipay, wechat, bank_transfer
    payment_id = Column(String)
    stripe_payment_intent_id = Column(String)
    metadata = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 關聯關係
    user = relationship("User", back_populates="orders")

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    type = Column(String, nullable=False)  # purchase, usage, refund, admin_adjustment
    amount = Column(Integer, nullable=False)  # 正數為增加，負數為減少
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    description = Column(String)
    metadata = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # 關聯關係
    user = relationship("User", back_populates="credit_transactions")

class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_type = Column(String, nullable=False)  # k2_chat, mirror_code, claude_editor
    provider = Column(String)  # infini-ai-cloud, moonshot-official
    tokens_used = Column(Integer, default=0)
    credits_consumed = Column(Integer, nullable=False)
    request_id = Column(String)
    metadata = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # 關聯關係
    user = relationship("User", back_populates="usage_logs")

# 創建表
Base.metadata.create_all(bind=engine)

# Pydantic 模型
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    credits: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    credits: int
    payment_method: str = "stripe"

class OrderResponse(BaseModel):
    id: int
    order_number: str
    amount: float
    currency: str
    credits: int
    status: str
    payment_method: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CreditTransactionResponse(BaseModel):
    id: int
    type: str
    amount: int
    balance_before: int
    balance_after: int
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UsageLogResponse(BaseModel):
    id: int
    service_type: str
    provider: Optional[str]
    tokens_used: int
    credits_consumed: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_orders: int
    total_revenue: float
    credits_sold: int
    credits_used: int

# 數據庫依賴
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 密碼哈希
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# JWT 工具
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 獲取當前用戶
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# 管理員權限檢查
def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# 生成訂單號
def generate_order_number() -> str:
    import time
    import random
    timestamp = int(time.time())
    random_part = random.randint(1000, 9999)
    return f"PA{timestamp}{random_part}"

# 積分價格計算
def calculate_credit_price(credits: int) -> float:
    """計算積分價格（人民幣）"""
    if credits <= 100:
        return credits * 0.10  # 0.1元/積分
    elif credits <= 500:
        return credits * 0.09  # 10% 折扣
    elif credits <= 1000:
        return credits * 0.08  # 20% 折扣
    else:
        return credits * 0.07  # 30% 折扣

# 積分交易記錄
def create_credit_transaction(db: Session, user_id: int, type: str, amount: int, 
                            description: str = None, order_id: int = None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    balance_before = user.credits
    balance_after = balance_before + amount
    
    # 更新用戶積分
    user.credits = balance_after
    
    # 創建交易記錄
    transaction = CreditTransaction(
        user_id=user_id,
        order_id=order_id,
        type=type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        description=description
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

# 應用生命周期
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時初始化 Redis
    redis_client = redis.from_url(REDIS_URL)
    await FastAPILimiter.init(redis_client)
    
    # 創建默認管理員用戶
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@powerauto.com").first()
        if not admin:
            admin = User(
                email="admin@powerauto.com",
                username="admin",
                password_hash=hash_password("admin123"),
                full_name="System Administrator",
                is_admin=True,
                credits=10000
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin user created")
    finally:
        db.close()
    
    yield
    
    # 關閉時清理
    await FastAPILimiter.close()

# FastAPI 應用
app = FastAPI(
    title="PowerAutomation 積分系統",
    description="支持500人同時在線的充值積分系統",
    version="1.0.0",
    lifespan=lifespan
)

# 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 健康檢查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# 用戶認證
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 檢查用戶是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # 創建新用戶
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        credits=100  # 註冊送100積分
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 創建積分交易記錄
    create_credit_transaction(
        db, user.id, "registration_bonus", 100, "註冊獎勵積分"
    )
    
    return user

@app.post("/api/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account disabled")
    
    # 創建 JWT token
    access_token = create_access_token(data={"user_id": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

# 用戶信息
@app.get("/api/user/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/api/user/credits")
async def get_credits(current_user: User = Depends(get_current_user)):
    return {
        "credits": current_user.credits,
        "user_id": current_user.id
    }

# 訂單管理
@app.post("/api/orders", response_model=OrderResponse)
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 計算價格
    amount = calculate_credit_price(order_data.credits)
    order_number = generate_order_number()
    
    # 創建訂單
    order = Order(
        user_id=current_user.id,
        order_number=order_number,
        amount=amount,
        credits=order_data.credits,
        payment_method=order_data.payment_method,
        metadata=json.dumps({"created_by": "api"})
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # 如果是 Stripe 支付，創建 PaymentIntent
    if order_data.payment_method == "stripe":
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe 使用分為單位
                currency="cny",
                metadata={
                    "order_id": order.id,
                    "user_id": current_user.id,
                    "credits": order_data.credits
                }
            )
            order.stripe_payment_intent_id = intent.id
            db.commit()
            
            return {
                **OrderResponse.from_orm(order).dict(),
                "client_secret": intent.client_secret
            }
        except Exception as e:
            logger.error(f"Stripe error: {e}")
            raise HTTPException(status_code=500, detail="Payment processing error")
    
    return order

@app.get("/api/orders", response_model=List[OrderResponse])
async def get_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders

@app.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# 支付回調
@app.post("/api/payments/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        order_id = payment_intent["metadata"]["order_id"]
        
        # 更新訂單狀態
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = "paid"
            order.payment_id = payment_intent["id"]
            
            # 增加用戶積分
            create_credit_transaction(
                db, order.user_id, "purchase", order.credits, 
                f"購買積分 - 訂單 {order.order_number}", order.id
            )
            
            db.commit()
    
    return {"status": "success"}

# 積分交易記錄
@app.get("/api/credits/transactions", response_model=List[CreditTransactionResponse])
async def get_credit_transactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transactions = db.query(CreditTransaction).filter(
        CreditTransaction.user_id == current_user.id
    ).order_by(CreditTransaction.created_at.desc()).limit(100).all()
    return transactions

# 使用記錄
@app.get("/api/usage/logs", response_model=List[UsageLogResponse])
async def get_usage_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logs = db.query(UsageLog).filter(
        UsageLog.user_id == current_user.id
    ).order_by(UsageLog.created_at.desc()).limit(100).all()
    return logs

# 記錄積分使用
@app.post("/api/usage/record")
async def record_usage(
    service_type: str,
    credits_consumed: int,
    provider: Optional[str] = None,
    tokens_used: int = 0,
    request_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 檢查積分是否足夠
    if current_user.credits < credits_consumed:
        raise HTTPException(status_code=400, detail="Insufficient credits")
    
    # 創建使用記錄
    usage_log = UsageLog(
        user_id=current_user.id,
        service_type=service_type,
        provider=provider,
        tokens_used=tokens_used,
        credits_consumed=credits_consumed,
        request_id=request_id
    )
    
    db.add(usage_log)
    
    # 扣除積分
    create_credit_transaction(
        db, current_user.id, "usage", -credits_consumed,
        f"使用 {service_type} 服務"
    )
    
    db.commit()
    
    return {"status": "success", "remaining_credits": current_user.credits}

# 管理員 API
@app.get("/api/admin/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_orders = db.query(Order).count()
    total_revenue = db.query(func.sum(Order.amount)).filter(Order.status == "paid").scalar() or 0
    credits_sold = db.query(func.sum(Order.credits)).filter(Order.status == "paid").scalar() or 0
    credits_used = db.query(func.sum(UsageLog.credits_consumed)).scalar() or 0
    
    return DashboardStats(
        total_users=total_users,
        active_users=active_users,
        total_orders=total_orders,
        total_revenue=total_revenue,
        credits_sold=credits_sold,
        credits_used=credits_used
    )

@app.get("/api/admin/users", response_model=List[UserResponse])
async def get_all_users(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users

@app.get("/api/admin/orders", response_model=List[OrderResponse])
async def get_all_orders(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return orders

# 速率限制
@app.get("/api/limited", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def limited_endpoint():
    return {"message": "This endpoint is rate limited"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4
    )