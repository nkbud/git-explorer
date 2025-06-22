"""This module defines the FastAPI router for the tree explorer feature."""

import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from gitingest.query_parsing import parse_query
from gitingest.cloning import clone_repo
from gitingest.schemas import FileSystemNode, FileSystemNodeType, FileSystemStats
from pathlib import Path
from server.server_config import templates
from server.server_utils import limiter

router = APIRouter()


def _filesystem_node_to_json(node: FileSystemNode) -> Dict[str, Any]:
    """
    Convert a FileSystemNode to a JSON-serializable dictionary.
    
    For files, includes content. For directories, includes children.
    Each node has metadata like type, size, extension, etc.
    """
    result = {
        "name": node.name,
        "type": node.type.name.lower(),
        "path": node.path_str,
        "size": node.size,
        "depth": node.depth,
        "file_count": node.file_count,
        "dir_count": node.dir_count,
    }
    
    if node.type == FileSystemNodeType.FILE:
        # For files, add content and extension
        result["content"] = node.content
        result["extension"] = node.path.suffix.lower() if node.path.suffix else ""
    elif node.type == FileSystemNodeType.DIRECTORY:
        # For directories, add children
        result["children"] = [_filesystem_node_to_json(child) for child in node.children]
    
    return result


@router.get("/tree-explorer", response_class=HTMLResponse)
async def tree_explorer_page(request: Request) -> HTMLResponse:
    """
    Render the tree explorer page.
    
    This page provides a game-like interface for exploring repository structures
    with D3.js visualization.
    """
    return templates.TemplateResponse(
        "tree_explorer.jinja",
        {"request": request}
    )


@router.post("/api/tree-data", response_class=JSONResponse)
@limiter.limit("5/minute")
async def get_tree_data(
    request: Request,
    repo_url: str = Form(...),
    token: str = Form(""),
    max_file_size: int = Form(10 * 1024 * 1024),  # 10MB default
) -> JSONResponse:
    """
    Clone a repository and return its structure as JSON for tree visualization.
    
    This endpoint processes a git repository URL and returns the complete
    file structure as a nested JSON object suitable for D3.js tree visualization.
    """
    try:
        # Parse the repository URL
        resolved_token = None if token == "" else token
        query = await parse_query(
            repo_url, 
            max_file_size=max_file_size,
            from_web=True,
            token=resolved_token
        )
        
        # Clone the repository
        clone_config = query.extract_clone_config()
        await clone_repo(clone_config, token=resolved_token)
        
        # Process the repository to get file structure
        from gitingest.ingestion import _process_node
        from gitingest.schemas import FileSystemStats
        from pathlib import Path
        
        subpath = Path(query.subpath.strip("/")).as_posix()
        path = query.local_path / subpath
        
        # Create root node similar to ingest_query
        root_node = FileSystemNode(
            name=path.name or query.slug,
            type=FileSystemNodeType.DIRECTORY if path.is_dir() else FileSystemNodeType.FILE,
            path_str=str(path.relative_to(query.local_path)),
            path=path,
        )
        
        if path.is_dir():
            stats = FileSystemStats()
            _process_node(
                node=root_node,
                query=query,
                stats=stats,
            )
        
        # Convert to JSON structure
        json_data = _filesystem_node_to_json(root_node)
        
        # Create a simple summary
        summary = f"Repository: {query.slug}\nFiles: {root_node.file_count}\nDirectories: {root_node.dir_count}"
        
        # Check for empty repository
        if root_node.file_count == 0 and root_node.dir_count == 0:
            summary += "\nNote: Repository appears to be empty"
        
        return JSONResponse(content={
            "success": True,
            "data": json_data,
            "summary": summary,
            "repo_info": {
                "url": query.url,
                "slug": query.slug,
                "user_name": query.user_name,
                "repo_name": query.repo_name,
                "total_files": root_node.file_count,
                "total_dirs": root_node.dir_count,
            }
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e)
            }
        )