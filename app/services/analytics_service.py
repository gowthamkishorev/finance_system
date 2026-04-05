from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict
from datetime import datetime
from typing import Optional

from app.models.transaction import Transaction, TransactionType
from app.models.user import User, UserRole
from app.schemas import FinancialSummary, CategoryBreakdown, MonthlyTotals, TransactionOut


def build_summary(db: Session, user: User, owner_id_filter: Optional[int] = None) -> FinancialSummary:
    """
    Compute a full financial summary.
    - Viewer: sees only their own data.
    - Analyst/Admin: can see all data or filter by a specific owner.
    """
    query = db.query(Transaction)

    if user.role == UserRole.viewer:
        query = query.filter(Transaction.owner_id == user.id)
    elif owner_id_filter is not None:
        query = query.filter(Transaction.owner_id == owner_id_filter)

    transactions = query.order_by(Transaction.date.desc()).all()

    total_income = sum(t.amount for t in transactions if t.type == TransactionType.income)
    total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.expense)
    balance = total_income - total_expenses

    # Category-wise breakdown
    category_map: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "count": 0})
    for t in transactions:
        category_map[t.category.value]["total"] += t.amount
        category_map[t.category.value]["count"] += 1

    category_breakdown = [
        CategoryBreakdown(category=cat, total=round(data["total"], 2), count=data["count"])
        for cat, data in sorted(category_map.items(), key=lambda x: x[1]["total"], reverse=True)
    ]

    # Monthly totals (YYYY-MM format)
    monthly_map: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for t in transactions:
        key = t.date.strftime("%Y-%m")
        if t.type == TransactionType.income:
            monthly_map[key]["income"] += t.amount
        else:
            monthly_map[key]["expenses"] += t.amount

    monthly_totals = [
        MonthlyTotals(
            month=month,
            income=round(data["income"], 2),
            expenses=round(data["expenses"], 2),
            net=round(data["income"] - data["expenses"], 2),
        )
        for month, data in sorted(monthly_map.items(), reverse=True)
    ]

    recent_transactions = transactions[:10]

    return FinancialSummary(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        balance=round(balance, 2),
        transaction_count=len(transactions),
        category_breakdown=category_breakdown,
        monthly_totals=monthly_totals,
        recent_transactions=[TransactionOut.model_validate(t) for t in recent_transactions],
    )
