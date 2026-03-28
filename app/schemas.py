"""
Pydantic schemas for request validation and response serialization.
Keeping these separate from SQLAlchemy models is just good practice.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


# --- Bank schemas ---

class BankBase(BaseModel):
    id: int
    name: str


class BankResponse(BankBase):
    """What a bank looks like in API responses."""

    model_config = ConfigDict(from_attributes=True)


class BankDetailResponse(BankBase):
    """Bank with its branch count - useful for the list endpoint."""
    branch_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# --- Branch schemas ---

class BranchBase(BaseModel):
    ifsc: str
    branch: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None


class BranchResponse(BranchBase):
    """Branch info with the bank name included."""
    bank_id: int
    bank_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Paginated response wrapper ---

class PaginatedResponse(BaseModel):
    """Generic wrapper for paginated results."""
    total: int = Field(description="Total number of records matching the query")
    limit: int = Field(description="Max records per page")
    offset: int = Field(description="Current offset")
    data: List = Field(description="The actual results")
