from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas import FinancialSummary
from app.auth import get_current_user, require_role
from app.services.analytics_service import build_summary

router = APIRouter()


@router.get("/summary", response_model=FinancialSummary)
def get_summary(
    owner_id: Optional[int] = Query(None, description="Filter by user (admin/analyst only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a full financial summary including totals, category breakdown, and monthly trends.
    - Viewers: see only their own data (owner_id param ignored).
    - Analysts/Admins: see all data, or filter by a specific user with ?owner_id=<id>.
    """
    return build_summary(db=db, user=current_user, owner_id_filter=owner_id)
