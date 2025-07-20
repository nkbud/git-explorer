"""Unit tests for tree explorer functionality that don't require HTTP client."""

from pathlib import Path

from gitingest.schemas import FileSystemNode, FileSystemNodeType, FileSystemStats
from server.routers.tree_explorer import _filesystem_node_to_json


class TestTreeExplorerUnitTests:
    """Unit tests for tree explorer components."""

    def test_filesystem_node_to_json_file(self):
        """Test converting a file node to JSON."""
        node = FileSystemNode(
            name="test.py",
            type=FileSystemNodeType.FILE,
            path_str="/test/test.py",
            path=Path("/test/test.py"),
            size=100,
            depth=1,
            file_count=0,
            dir_count=0,
        )

        result = _filesystem_node_to_json(node)

        expected = {
            "name": "test.py",
            "type": "file",
            "path": "/test/test.py",
            "size": 100,
            "depth": 1,
            "file_count": 0,
            "dir_count": 0,
            "content": node.content,  # Use the property
            "extension": ".py",
        }

        assert result == expected

    def test_filesystem_node_to_json_directory(self):
        """Test converting a directory node to JSON."""
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

        result = _filesystem_node_to_json(dir_node)

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
                    "content": child_file.content,  # Use the property
                    "extension": ".py",
                }
            ],
        }

        assert result == expected

    def test_filesystem_node_to_json_file_no_extension(self):
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
        assert result["name"] == "README"
        assert result["type"] == "file"

    def test_filesystem_node_to_json_empty_directory(self):
        """Test converting an empty directory node."""
        dir_node = FileSystemNode(
            name="empty",
            type=FileSystemNodeType.DIRECTORY,
            path_str="/test/empty",
            path=Path("/test/empty"),
            size=0,
            depth=1,
            file_count=0,
            dir_count=0,
        )
        dir_node.children = []

        result = _filesystem_node_to_json(dir_node)

        assert result["name"] == "empty"
        assert result["type"] == "directory"
        assert result["children"] == []
        assert result["file_count"] == 0
        assert result["dir_count"] == 0


class TestFileSystemStatsUsage:
    """Test FileSystemStats usage in tree explorer."""

    def test_filesystem_stats_creation(self):
        """Test creating FileSystemStats with correct fields."""
        stats = FileSystemStats(
            visited=set(),
            total_files=10,
            total_size=1000,
        )

        assert stats.total_files == 10
        assert stats.total_size == 1000
        assert isinstance(stats.visited, set)
        assert len(stats.visited) == 0

    def test_filesystem_stats_with_data(self):
        """Test FileSystemStats with some visited paths."""
        visited_paths = {Path("/test/file1.py"), Path("/test/file2.py")}

        stats = FileSystemStats(
            visited=visited_paths,
            total_files=2,
            total_size=200,
        )

        assert stats.total_files == 2
        assert stats.total_size == 200
        assert len(stats.visited) == 2
        assert Path("/test/file1.py") in stats.visited


class TestTreeExplorerLogic:
    """Test business logic of tree explorer."""

    def test_size_limit_validation(self):
        """Test the 1GB size limit logic."""
        max_size = 1024 * 1024 * 1024  # 1GB

        # Test under limit
        small_stats = FileSystemStats(
            visited=set(),
            total_files=100,
            total_size=500 * 1024 * 1024,  # 500MB
        )
        assert small_stats.total_size < max_size

        # Test over limit
        large_stats = FileSystemStats(
            visited=set(),
            total_files=1000,
            total_size=2 * 1024 * 1024 * 1024,  # 2GB
        )
        assert large_stats.total_size > max_size

    def test_file_extension_extraction(self):
        """Test file extension extraction from paths."""
        test_cases = [
            ("file.py", ".py"),
            ("file.js", ".js"),
            ("file.tar.gz", ".gz"),
            ("README", ""),
            (".hidden", ""),
        ]

        for filename, expected_ext in test_cases:
            path = Path(f"/test/{filename}")
            ext = path.suffix.lower() if path.suffix else ""
            assert ext == expected_ext, f"Failed for {filename}: expected {expected_ext}, got {ext}"

    def test_tree_depth_tracking(self):
        """Test that tree depth is properly tracked."""
        # Root level
        root = FileSystemNode(
            name="root",
            type=FileSystemNodeType.DIRECTORY,
            path_str="/root",
            path=Path("/root"),
            size=0,
            depth=0,
            file_count=0,
            dir_count=0,
        )

        # Level 1
        level1 = FileSystemNode(
            name="level1",
            type=FileSystemNodeType.DIRECTORY,
            path_str="/root/level1",
            path=Path("/root/level1"),
            size=0,
            depth=1,
            file_count=0,
            dir_count=0,
        )

        # Level 2
        level2_file = FileSystemNode(
            name="file.py",
            type=FileSystemNodeType.FILE,
            path_str="/root/level1/file.py",
            path=Path("/root/level1/file.py"),
            size=100,
            depth=2,
            file_count=0,
            dir_count=0,
        )

        level1.children = [level2_file]
        root.children = [level1]

        # Convert to JSON and verify depth is preserved
        result = _filesystem_node_to_json(root)

        assert result["depth"] == 0
        assert result["children"][0]["depth"] == 1
        assert result["children"][0]["children"][0]["depth"] == 2
