from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
from app.models.transaction import TransactionType, Category


# ── Auth Schemas ────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: UserRole


# ── User Schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.viewer

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores allowed).")
        return v.lower()


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Transaction Schemas ───────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be greater than 0.")
    type: TransactionType
    category: Category = Category.other
    date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[TransactionType] = None
    category: Optional[Category] = None
    date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class TransactionOut(BaseModel):
    id: int
    amount: float
    type: TransactionType
    category: Category
    date: datetime
    notes: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedTransactions(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TransactionOut]


# ── Analytics Schemas ─────────────────────────────────────────────────────────

class CategoryBreakdown(BaseModel):
    category: str
    total: float
    count: int


class MonthlyTotals(BaseModel):
    month: str  # "YYYY-MM"
    income: float
    expenses: float
    net: float


class FinancialSummary(BaseModel):
    total_income: float
    total_expenses: float
    balance: float
    transaction_count: int
    category_breakdown: list[CategoryBreakdown]
    monthly_totals: list[MonthlyTotals]
    recent_transactions: list[TransactionOut]
