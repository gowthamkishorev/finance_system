from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User, UserRole
from app.models.transaction import TransactionType, Category
from app.schemas import TransactionCreate, TransactionUpdate, TransactionOut, PaginatedTransactions
from app.auth import get_current_user, require_role
from app.services.transaction_service import (
    create_transaction,
    list_transactions,
    update_transaction,
    delete_transaction,
    get_transaction_or_404,
    can_access_transaction,
)

router = APIRouter()


@router.post("/", response_model=TransactionOut, status_code=201)
def create(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
):
    """Create a new transaction. Analyst and Admin only."""
    return create_transaction(payload, owner_id=current_user.id, db=db)


@router.get("/", response_model=PaginatedTransactions)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[TransactionType] = Query(None),
    category: Optional[Category] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    owner_id: Optional[int] = Query(None, description="Filter by user ID (admin/analyst only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List transactions with optional filters.
    - Viewers see only their own.
    - Analysts/Admins see all, and can filter by owner_id.
    """
    total, items = list_transactions(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
        type_filter=type,
        category_filter=category,
        start_date=start_date,
        end_date=end_date,
        owner_id_filter=owner_id,
    )
    return PaginatedTransactions(total=total, page=page, page_size=page_size, items=items)


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_one(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single transaction by ID."""
    from fastapi import HTTPException
    t = get_transaction_or_404(transaction_id, db)
    if not can_access_transaction(t, current_user):
        raise HTTPException(status_code=403, detail="Access denied.")
    return t


@router.patch("/{transaction_id}", response_model=TransactionOut)
def update(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
):
    """Update a transaction. Owner (analyst) or Admin."""
    return update_transaction(transaction_id, payload, current_user, db)


@router.delete("/{transaction_id}", status_code=204)
def delete(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
):
    """Delete a transaction. Owner (analyst) or Admin."""
    delete_transaction(transaction_id, current_user, db)
