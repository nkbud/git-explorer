"""This module contains the routers for the FastAPI application."""

from server.routers.download import router as download
from server.routers.dynamic import router as dynamic
from server.routers.index import router as index
from server.routers.tree_explorer import router as tree_explorer

__all__ = ["download", "dynamic", "index", "tree_explorer"]
