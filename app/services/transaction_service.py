from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone
from typing import Optional

from app.models.transaction import Transaction, TransactionType, Category
from app.models.user import User, UserRole
from app.schemas import TransactionCreate, TransactionUpdate
from fastapi import HTTPException


def get_transaction_or_404(transaction_id: int, db: Session) -> Transaction:
    t = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return t


def can_access_transaction(transaction: Transaction, user: User) -> bool:
    """Admins and analysts can see all; viewers only see their own."""
    if user.role in (UserRole.admin, UserRole.analyst):
        return True
    return transaction.owner_id == user.id


def create_transaction(payload: TransactionCreate, owner_id: int, db: Session) -> Transaction:
    date = payload.date or datetime.now(timezone.utc)
    t = Transaction(
        amount=payload.amount,
        type=payload.type,
        category=payload.category,
        date=date,
        notes=payload.notes,
        owner_id=owner_id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def list_transactions(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    type_filter: Optional[TransactionType] = None,
    category_filter: Optional[Category] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    owner_id_filter: Optional[int] = None,
):
    query = db.query(Transaction)

    # Viewers only see their own transactions
    if user.role == UserRole.viewer:
        query = query.filter(Transaction.owner_id == user.id)
    elif owner_id_filter is not None:
        query = query.filter(Transaction.owner_id == owner_id_filter)

    if type_filter:
        query = query.filter(Transaction.type == type_filter)
    if category_filter:
        query = query.filter(Transaction.category == category_filter)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    total = query.count()
    items = query.order_by(Transaction.date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def update_transaction(transaction_id: int, payload: TransactionUpdate, user: User, db: Session) -> Transaction:
    t = get_transaction_or_404(transaction_id, db)

    # Only admins or the owner can update
    if user.role != UserRole.admin and t.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You do not own this transaction.")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(t, field, value)
    t.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(t)
    return t


def delete_transaction(transaction_id: int, user: User, db: Session) -> None:
    t = get_transaction_or_404(transaction_id, db)

    if user.role != UserRole.admin and t.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You do not own this transaction.")

    db.delete(t)
    db.commit()
