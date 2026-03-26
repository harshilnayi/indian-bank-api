"""
REST API routes for bank and branch data.

Endpoints:
  GET /api/banks          - list all banks (paginated)
  GET /api/banks/{id}     - get a specific bank by id  
  GET /api/banks/{id}/branches - branches for a given bank
  GET /api/branches/{ifsc} - look up a branch by IFSC code
  GET /api/branches/search - search/filter branches by city, state, etc
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.models import Bank, Branch
from app.schemas import (
    BankResponse,
    BankDetailResponse,
    BranchResponse,
    PaginatedResponse,
)

router = APIRouter(prefix="/api", tags=["REST API"])


@router.get("/banks", response_model=PaginatedResponse)
def list_banks(
    limit: int = Query(default=20, ge=1, le=100, description="Results per page"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
):
    """Get a paginated list of all banks with their branch counts."""

    total = db.query(func.count(Bank.id)).scalar()

    # grab banks and count their branches in one go
    banks_query = (
        db.query(Bank, func.count(Branch.ifsc).label("branch_count"))
        .outerjoin(Branch, Bank.id == Branch.bank_id)
        .group_by(Bank.id)
        .order_by(Bank.name)
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for bank, count in banks_query:
        results.append(
            BankDetailResponse(
                id=bank.id,
                name=bank.name,
                branch_count=count,
            )
        )

    return PaginatedResponse(total=total, limit=limit, offset=offset, data=results)


@router.get("/banks/{bank_id}", response_model=BankDetailResponse)
def get_bank(bank_id: int, db: Session = Depends(get_db)):
    """Get details of a single bank by its ID."""

    result = (
        db.query(Bank, func.count(Branch.ifsc).label("branch_count"))
        .outerjoin(Branch, Bank.id == Branch.bank_id)
        .filter(Bank.id == bank_id)
        .group_by(Bank.id)
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"No bank found with id {bank_id}")

    bank, count = result
    return BankDetailResponse(id=bank.id, name=bank.name, branch_count=count)


@router.get("/banks/{bank_id}/branches", response_model=PaginatedResponse)
def list_bank_branches(
    bank_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Get all branches belonging to a specific bank."""

    # first check if bank exists
    bank = db.query(Bank).filter(Bank.id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail=f"No bank found with id {bank_id}")

    total = db.query(func.count(Branch.ifsc)).filter(Branch.bank_id == bank_id).scalar()
    
    branches = (
        db.query(Branch)
        .filter(Branch.bank_id == bank_id)
        .order_by(Branch.branch)
        .offset(offset)
        .limit(limit)
        .all()
    )

    data = [
        BranchResponse(
            ifsc=b.ifsc,
            bank_id=b.bank_id,
            branch=b.branch,
            address=b.address,
            city=b.city,
            district=b.district,
            state=b.state,
            bank_name=bank.name,
        )
        for b in branches
    ]

    return PaginatedResponse(total=total, limit=limit, offset=offset, data=data)


@router.get("/branches/search", response_model=PaginatedResponse)
def search_branches(
    q: Optional[str] = Query(default=None, description="Search term for branch name"),
    city: Optional[str] = Query(default=None, description="Filter by city"),
    state: Optional[str] = Query(default=None, description="Filter by state"),
    bank_name: Optional[str] = Query(default=None, description="Filter by bank name"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Search and filter branches.
    You can combine multiple filters - they all stack (AND logic).
    """

    query = db.query(Branch).join(Bank, Branch.bank_id == Bank.id)

    # apply filters
    if q:
        query = query.filter(Branch.branch.ilike(f"%{q}%"))
    if city:
        query = query.filter(Branch.city.ilike(f"%{city}%"))
    if state:
        query = query.filter(Branch.state.ilike(f"%{state}%"))
    if bank_name:
        query = query.filter(Bank.name.ilike(f"%{bank_name}%"))

    total = query.count()
    branches = query.order_by(Branch.ifsc).offset(offset).limit(limit).all()

    data = [
        BranchResponse(
            ifsc=b.ifsc,
            bank_id=b.bank_id,
            branch=b.branch,
            address=b.address,
            city=b.city,
            district=b.district,
            state=b.state,
            bank_name=b.bank.name if b.bank else None,
        )
        for b in branches
    ]

    return PaginatedResponse(total=total, limit=limit, offset=offset, data=data)


@router.get("/branches/{ifsc}", response_model=BranchResponse)
def get_branch(ifsc: str, db: Session = Depends(get_db)):
    """Look up a specific branch by its IFSC code."""

    branch = db.query(Branch).filter(Branch.ifsc == ifsc.upper()).first()

    if not branch:
        raise HTTPException(
            status_code=404, detail=f"No branch found with IFSC code '{ifsc}'"
        )

    return BranchResponse(
        ifsc=branch.ifsc,
        bank_id=branch.bank_id,
        branch=branch.branch,
        address=branch.address,
        city=branch.city,
        district=branch.district,
        state=branch.state,
        bank_name=branch.bank.name if branch.bank else None,
    )
