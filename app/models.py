"""
SQLAlchemy models for banks and branches.

Schema is based on the indian_banks dataset:
  - banks table: id + name
  - branches table: ifsc (PK), bank_id (FK), branch name, address, city, district, state
"""

from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Bank(Base):
    __tablename__ = "banks"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(49), nullable=False)

    # one bank has many branches
    branches = relationship("Branch", back_populates="bank", lazy="dynamic")

    def __repr__(self):
        return f"<Bank(id={self.id}, name='{self.name}')>"


class Branch(Base):
    __tablename__ = "branches"

    ifsc = Column(String(11), primary_key=True, index=True)
    bank_id = Column(BigInteger, ForeignKey("banks.id"), nullable=False, index=True)
    branch = Column(String(74))
    address = Column(String(195))
    city = Column(String(50), index=True)
    district = Column(String(50))
    state = Column(String(26), index=True)

    # relationship back to bank
    bank = relationship("Bank", back_populates="branches")

    def __repr__(self):
        return f"<Branch(ifsc='{self.ifsc}', branch='{self.branch}')>"
