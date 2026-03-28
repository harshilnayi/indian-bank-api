"""
Main application entry point.

Mounts:
  - REST API at /api/*
  - GraphQL playground at /gql
  - Root endpoint with basic API info
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from app.routers.banks import router as banks_router
from app.graphql.schema import schema

app = FastAPI(
    title="Indian Banks API",
    description=(
        "API service for querying Indian bank branch data. "
        "Supports both REST and GraphQL interfaces. "
        "Data sourced from RBI's bank branch records."
    ),
    version="1.0.0",
)

# allow cross-origin requests (useful if someone builds a frontend for this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount the REST routes
app.include_router(banks_router)

# mount GraphQL - the assignment specifically asks for this at /gql
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/gql")


@app.get("/", tags=["Root"])
def root():
    """Landing page with links to the different interfaces."""
    return {
        "message": "Indian Banks API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "rest_api": "/api/banks",
            "graphql": "/gql",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Lightweight health endpoint for deployments and smoke tests."""
    return {"status": "ok"}
