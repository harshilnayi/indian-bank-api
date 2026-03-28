"""
GraphQL schema using Strawberry.

Exposes bank and branch data via GraphQL at /gql.
Supports the relay-style connection pattern (edges/node) as shown
in the assignment requirements.
"""

from typing import List, Optional

import strawberry
from graphql import GraphQLError

from app.database import SessionLocal
from app.models import Bank as BankModel, Branch as BranchModel


# --- GraphQL Types ---

@strawberry.type
class BankType:
    """Represents a bank entity."""
    id: int
    name: str


@strawberry.type
class BranchType:
    """Represents a single branch with its associated bank info."""
    ifsc: str
    branch: Optional[str]
    address: Optional[str]
    city: Optional[str]
    district: Optional[str]
    state: Optional[str]
    bank: Optional[BankType]


@strawberry.type
class BranchEdge:
    """Wraps a branch in the relay-style edge format."""
    node: BranchType


@strawberry.type
class BranchConnection:
    """
    Relay-style connection for paginating through branches.
    Keeps things compatible with the sample query from the assignment.
    """
    edges: List[BranchEdge]
    total_count: int


# helper to convert db row -> graphql type
def _branch_to_type(branch_row) -> BranchType:
    bank_type = None
    if branch_row.bank:
        bank_type = BankType(id=branch_row.bank.id, name=branch_row.bank.name)

    return BranchType(
        ifsc=branch_row.ifsc,
        branch=branch_row.branch,
        address=branch_row.address,
        city=branch_row.city,
        district=branch_row.district,
        state=branch_row.state,
        bank=bank_type,
    )


# --- Queries ---

@strawberry.type
class Query:

    @strawberry.field
    def branches(
        self,
        first: Optional[int] = 20,
        offset: Optional[int] = 0,
        city: Optional[str] = None,
        state: Optional[str] = None,
        bank_id: Optional[int] = None,
    ) -> BranchConnection:
        """
        Query branches with optional filtering.
        Uses pagination to avoid dumping 100k+ records at once.
        """
        db = SessionLocal()
        try:
            query = db.query(BranchModel)

            if city:
                query = query.filter(BranchModel.city.ilike(f"%{city}%"))
            if state:
                query = query.filter(BranchModel.state.ilike(f"%{state}%"))
            if bank_id:
                query = query.filter(BranchModel.bank_id == bank_id)

            total = query.count()

            actual_offset = offset or 0
            if actual_offset < 0:
                raise GraphQLError("offset must be greater than or equal to 0")

            if first is None:
                actual_limit = 20
            elif first < 0:
                raise GraphQLError("first must be greater than or equal to 0")
            else:
                # cap first at 100 so nobody tries to pull everything at once
                actual_limit = min(first, 100)

            rows = (
                query.order_by(BranchModel.ifsc)
                .offset(actual_offset)
                .limit(actual_limit)
                .all()
            )

            edges = [BranchEdge(node=_branch_to_type(row)) for row in rows]
            return BranchConnection(edges=edges, total_count=total)
        finally:
            db.close()

    @strawberry.field
    def branch(self, ifsc: str) -> Optional[BranchType]:
        """Look up a single branch by IFSC code."""
        db = SessionLocal()
        try:
            row = db.query(BranchModel).filter(BranchModel.ifsc == ifsc.upper()).first()
            if not row:
                return None
            return _branch_to_type(row)
        finally:
            db.close()

    @strawberry.field
    def banks(self, first: Optional[int] = 50, offset: Optional[int] = 0) -> List[BankType]:
        """Get a list of all banks."""
        db = SessionLocal()
        try:
            actual_offset = offset or 0
            if actual_offset < 0:
                raise GraphQLError("offset must be greater than or equal to 0")

            if first is None:
                actual_limit = 50
            elif first < 0:
                raise GraphQLError("first must be greater than or equal to 0")
            else:
                actual_limit = min(first, 200)

            rows = (
                db.query(BankModel)
                .order_by(BankModel.name)
                .offset(actual_offset)
                .limit(actual_limit)
                .all()
            )
            return [BankType(id=r.id, name=r.name) for r in rows]
        finally:
            db.close()

    @strawberry.field
    def bank(self, id: int) -> Optional[BankType]:
        """Get a specific bank by ID."""
        db = SessionLocal()
        try:
            row = db.query(BankModel).filter(BankModel.id == id).first()
            if not row:
                return None
            return BankType(id=row.id, name=row.name)
        finally:
            db.close()


schema = strawberry.Schema(query=Query)
