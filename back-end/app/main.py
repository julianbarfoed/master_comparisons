"""FastAPI application entry point.

Routers, middleware, and lifecycle configuration belong here once the API
contract is defined.
"""

from fastapi import FastAPI

app = FastAPI(title="Audio API", version="0.1.0")
