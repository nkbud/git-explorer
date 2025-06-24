"""Tests for the tree explorer feature."""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from gitingest.schemas import FileSystemNode, FileSystemNodeType, FileSystemStats
from server.main import app
from server.routers.tree_explorer import _filesystem_node_to_json


@pytest.fixture
def client():
    """Create a test client with proper host configuration."""
    # Set environment variable to allow test host
    with patch.dict(os.environ, {"ALLOWED_HOSTS": "testserver,localhost,127.0.0.1"}):
        return TestClient(app)


@pytest.fixture
def sample_file_node():
    """Create a sample file node for testing."""
    return FileSystemNode(
        name="test.py",
        type=FileSystemNodeType.FILE,
        path_str="/test/test.py",
        path=Path("/test/test.py"),
        size=100,
        depth=1,
        file_count=0,
        dir_count=0,
    )


@pytest.fixture
def sample_dir_node():
    """Create a sample directory node with children for testing."""
    # Create child file
    child_file = FileSystemNode(
        name="child.py",
        type=FileSystemNodeType.FILE,
        path_str="/test/src/child.py",
        path=Path("/test/src/child.py"),
        size=50,
        depth=2,
        file_count=0,
        dir_count=0,
    )
    
    # Create directory node
    dir_node = FileSystemNode(
        name="src",
        type=FileSystemNodeType.DIRECTORY,
        path_str="/test/src",
        path=Path("/test/src"),
        size=50,
        depth=1,
        file_count=1,
        dir_count=0,
    )
    dir_node.children = [child_file]
    
    return dir_node


class TestFileSystemNodeToJson:
    """Test the filesystem node to JSON conversion."""

    def test_file_node_conversion(self, sample_file_node):
        """Test converting a file node to JSON."""
        result = _filesystem_node_to_json(sample_file_node)
        
        expected = {
            "name": "test.py",
            "type": "file",
            "path": "/test/test.py",
            "size": 100,
            "depth": 1,
            "file_count": 0,
            "dir_count": 0,
            "content": sample_file_node.content,  # Use the property
            "extension": ".py",
        }
        
        assert result == expected

    def test_directory_node_conversion(self, sample_dir_node):
        """Test converting a directory node to JSON."""
        result = _filesystem_node_to_json(sample_dir_node)
        
        expected = {
            "name": "src",
            "type": "directory",
            "path": "/test/src",
            "size": 50,
            "depth": 1,
            "file_count": 1,
            "dir_count": 0,
            "children": [
                {
                    "name": "child.py",
                    "type": "file",
                    "path": "/test/src/child.py",
                    "size": 50,
                    "depth": 2,
                    "file_count": 0,
                    "dir_count": 0,
                    "content": sample_dir_node.children[0].content,  # Use the property
                    "extension": ".py",
                }
            ],
        }
        
        assert result == expected

    def test_file_without_extension(self):
        """Test converting a file node without extension."""
        node = FileSystemNode(
            name="README",
            type=FileSystemNodeType.FILE,
            path_str="/test/README",
            path=Path("/test/README"),
            size=100,
            depth=1,
            file_count=0,
            dir_count=0,
        )
        
        result = _filesystem_node_to_json(node)
        assert result["extension"] == ""


class TestTreeExplorerRoutes:
    """Test the tree explorer HTTP routes."""

    def test_tree_data_api_missing_url(self, client):
        """Test API endpoint with missing repository URL."""
        response = client.post("/api/tree-data")
        
        # Should return some error - could be 400 or 422 depending on validation
        assert response.status_code in [400, 422]

    def test_tree_data_api_invalid_url(self, client, mocker: MockerFixture):
        """Test API endpoint with invalid repository URL."""
        # Mock parse_query to raise validation error
        mock_parse_query = mocker.patch("server.routers.tree_explorer.parse_query")
        mock_parse_query.side_effect = ValueError("Invalid URL format")
        
        response = client.post(
            "/api/tree-data",
            data={"repository_url": "not-a-valid-url"}
        )
        
        assert response.status_code == 400
        if response.headers.get("content-type") == "application/json":
            data = response.json()
            assert "error" in data
            assert "Invalid URL format" in data["error"]

    def test_tree_data_api_rate_limit(self, client, mocker: MockerFixture):
        """Test API endpoint rate limiting."""
        # Mock the rate limiter to raise an exception
        mock_limiter = mocker.patch("server.routers.tree_explorer.limiter.limit")
        from slowapi.errors import RateLimitExceeded
        
        # Create a mock exception with proper error message format
        exception = RateLimitExceeded("5/minute")
        exception.detail = "5 per minute"
        mock_limiter.side_effect = exception
        
        response = client.post(
            "/api/tree-data",
            data={"repository_url": "https://github.com/user/repo"}
        )
        
        # The rate limit should be handled by the global exception handler
        assert response.status_code == 429

    def test_tree_data_api_success(self, client, mocker: MockerFixture, sample_dir_node):
        """Test successful API call with valid repository."""
        # Mock the cloning and parsing functions
        mock_parse_query = mocker.patch("server.routers.tree_explorer.parse_query")
        mock_clone_repo = mocker.patch("server.routers.tree_explorer.clone_repo")
        
        # Set up mock returns
        mock_query = MagicMock()
        mock_query.local_path = Path("/tmp/test-repo")
        mock_parse_query.return_value = mock_query
        
        mock_stats = FileSystemStats(
            visited=set(),
            total_files=2,
            total_size=150,
        )
        
        mock_clone_repo.return_value = (sample_dir_node, mock_stats)
        
        response = client.post(
            "/api/tree-data",
            data={"repository_url": "https://github.com/user/repo"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tree" in data
        assert "stats" in data
        assert data["tree"]["name"] == "src"
        assert data["tree"]["type"] == "directory"
        assert len(data["tree"]["children"]) == 1
        assert data["stats"]["total_files"] == 2

    def test_tree_data_api_with_token(self, client, mocker: MockerFixture, sample_file_node):
        """Test API call with GitHub token for private repos."""
        mock_parse_query = mocker.patch("server.routers.tree_explorer.parse_query")
        mock_clone_repo = mocker.patch("server.routers.tree_explorer.clone_repo")
        
        mock_query = MagicMock()
        mock_query.local_path = Path("/tmp/test-repo")
        mock_parse_query.return_value = mock_query
        
        mock_stats = FileSystemStats(
            visited=set(),
            total_files=1,
            total_size=100,
        )
        
        mock_clone_repo.return_value = (sample_file_node, mock_stats)
        
        response = client.post(
            "/api/tree-data",
            data={
                "repository_url": "https://github.com/user/private-repo",
                "github_token": "ghp_test_token"
            }
        )
        
        assert response.status_code == 200
        # Verify that parse_query was called with the token
        mock_parse_query.assert_called_once()
        call_args = mock_parse_query.call_args[0]
        assert "ghp_test_token" in call_args

    def test_tree_data_api_cloning_error(self, client, mocker: MockerFixture):
        """Test API handling of repository cloning errors."""
        mock_parse_query = mocker.patch("server.routers.tree_explorer.parse_query")
        mock_clone_repo = mocker.patch("server.routers.tree_explorer.clone_repo")
        
        mock_query = MagicMock()
        mock_parse_query.return_value = mock_query
        
        # Mock cloning to raise an exception
        mock_clone_repo.side_effect = Exception("Repository not found")
        
        response = client.post(
            "/api/tree-data",
            data={"repository_url": "https://github.com/user/nonexistent"}
        )
        
        assert response.status_code == 400
        # Check that response is JSON
        assert response.headers.get("content-type") == "application/json"
        data = response.json()
        assert "error" in data
        assert "Repository not found" in data["error"]

    def test_tree_data_api_large_repository_size_limit(self, client, mocker: MockerFixture):
        """Test API handling of repositories exceeding size limit."""
        mock_parse_query = mocker.patch("server.routers.tree_explorer.parse_query")
        mock_clone_repo = mocker.patch("server.routers.tree_explorer.clone_repo")
        
        mock_query = MagicMock()
        mock_parse_query.return_value = mock_query
        
        # Create a large stats object that exceeds the 1GB limit
        large_stats = FileSystemStats(
            visited=set(),
            total_files=1000,
            total_size=2_000_000_000,  # 2GB
        )
        
        sample_node = FileSystemNode(
            name="large-repo",
            type=FileSystemNodeType.DIRECTORY,
            path_str="/tmp/large-repo",
            path=Path("/tmp/large-repo"),
            size=2_000_000_000,
            depth=0,
            file_count=1000,
            dir_count=100,
        )
        
        mock_clone_repo.return_value = (sample_node, large_stats)
        
        response = client.post(
            "/api/tree-data",
            data={"repository_url": "https://github.com/user/large-repo"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "too large" in data["error"].lower()

    def test_tree_data_api_empty_repository(self, client, mocker: MockerFixture):
        """Test API handling of empty repositories."""
        mock_parse_query = mocker.patch("server.routers.tree_explorer.parse_query")
        mock_clone_repo = mocker.patch("server.routers.tree_explorer.clone_repo")
        
        mock_query = MagicMock()
        mock_query.local_path = Path("/tmp/empty-repo")
        mock_parse_query.return_value = mock_query
        
        # Create empty repository node
        empty_node = FileSystemNode(
            name="empty-repo",
            type=FileSystemNodeType.DIRECTORY,
            path_str="/tmp/empty-repo",
            path=Path("/tmp/empty-repo"),
            size=0,
            depth=0,
            file_count=0,
            dir_count=0,
        )
        empty_node.children = []
        
        empty_stats = FileSystemStats(
            visited=set(),
            total_files=0,
            total_size=0,
        )
        
        mock_clone_repo.return_value = (empty_node, empty_stats)
        
        response = client.post(
            "/api/tree-data",
            data={"repository_url": "https://github.com/user/empty-repo"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total_files"] == 0
        assert data["tree"]["children"] == []


class TestTreeExplorerIntegration:
    """Integration tests for the tree explorer feature."""

    def test_api_endpoint_cors_and_headers(self, client, mocker: MockerFixture):
        """Test that API endpoint returns proper headers."""
        # Mock to avoid actual cloning
        mock_parse_query = mocker.patch("server.routers.tree_explorer.parse_query")
        mock_clone_repo = mocker.patch("server.routers.tree_explorer.clone_repo")
        
        mock_query = MagicMock()
        mock_parse_query.return_value = mock_query
        mock_clone_repo.side_effect = Exception("Test error")
        
        response = client.post(
            "/api/tree-data",
            data={"repository_url": "https://github.com/user/test"}
        )
        
        # Should return JSON content type even for errors
        assert "application/json" in response.headers.get("content-type", "")

    def test_javascript_file_content(self):
        """Test that the tree explorer JavaScript file has expected content."""
        js_path = Path(__file__).parent.parent / "src" / "static" / "js" / "tree_explorer.js"
        
        if js_path.exists():
            content = js_path.read_text()
            # Check for key D3.js visualization elements
            assert "d3." in content
            assert "tree" in content.lower()
        else:
            pytest.skip("JavaScript file not found in expected location")


class TestTreeExplorerErrorHandling:
    """Test error handling in tree explorer."""

    def test_malformed_github_url(self, client, mocker: MockerFixture):
        """Test handling of malformed GitHub URLs."""
        # Mock to avoid actual processing
        mock_parse_query = mocker.patch("server.routers.tree_explorer.parse_query")
        mock_parse_query.side_effect = ValueError("Invalid URL format")
        
        test_urls = [
            "github.com/user/repo",  # Missing protocol
            "https://github.com/",   # Missing user/repo
            "https://github.com/user",  # Missing repo
            "https://notgithub.com/user/repo",  # Wrong domain
        ]
        
        for url in test_urls:
            response = client.post(
                "/api/tree-data",
                data={"repository_url": url}
            )
            assert response.status_code == 400, f"Failed for URL: {url}"
            if response.headers.get("content-type") == "application/json":
                data = response.json()
                assert "error" in data

    def test_network_timeout_handling(self, client, mocker: MockerFixture):
        """Test handling of network timeouts during cloning."""
        mock_parse_query = mocker.patch("server.routers.tree_explorer.parse_query")
        mock_clone_repo = mocker.patch("server.routers.tree_explorer.clone_repo")
        
        mock_query = MagicMock()
        mock_parse_query.return_value = mock_query
        
        # Simulate network timeout
        import asyncio
        mock_clone_repo.side_effect = asyncio.TimeoutError("Network timeout")
        
        response = client.post(
            "/api/tree-data",
            data={"repository_url": "https://github.com/user/slow-repo"}
        )
        
        assert response.status_code == 400
        if response.headers.get("content-type") == "application/json":
            data = response.json()
            assert "error" in data

    def test_invalid_github_token(self, client, mocker: MockerFixture):
        """Test handling of invalid GitHub tokens."""
        mock_parse_query = mocker.patch("server.routers.tree_explorer.parse_query")
        mock_clone_repo = mocker.patch("server.routers.tree_explorer.clone_repo")
        
        mock_query = MagicMock()
        mock_parse_query.return_value = mock_query
        
        # Simulate authentication error
        mock_clone_repo.side_effect = Exception("Bad credentials")
        
        response = client.post(
            "/api/tree-data",
            data={
                "repository_url": "https://github.com/user/private-repo",
                "github_token": "invalid_token"
            }
        )
        
        assert response.status_code == 400
        if response.headers.get("content-type") == "application/json":
            data = response.json()
            assert "error" in data
            assert "credentials" in data["error"].lower()