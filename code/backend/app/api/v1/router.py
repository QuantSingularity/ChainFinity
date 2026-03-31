"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter

from .endpoints import (auth, blockchain, compliance, portfolios, risk,
                        transactions, users)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(blockchain.router, prefix="/blockchain", tags=["blockchain"])
