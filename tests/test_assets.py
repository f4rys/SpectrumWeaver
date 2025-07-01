"""Tests for the assets resources module."""

from src.assets import resources


class TestResources:
    """Test cases for the resources module."""

    def test_resources_module_import(self) -> None:
        """Test that the resources module can be imported."""
        assert resources is not None

    def test_qt_resource_data_exists(self) -> None:
        """Test that qt_resource_data is defined."""
        assert hasattr(resources, 'qt_resource_data')
        assert isinstance(resources.qt_resource_data, bytes)

    def test_qt_resource_data_not_empty(self) -> None:
        """Test that qt_resource_data contains data."""
        assert len(resources.qt_resource_data) > 0

    def test_qt_resource_name_exists(self) -> None:
        """Test that qt_resource_name is defined."""
        assert hasattr(resources, 'qt_resource_name')
        assert isinstance(resources.qt_resource_name, bytes)

    def test_qt_resource_struct_exists(self) -> None:
        """Test that qt_resource_struct is defined."""
        assert hasattr(resources, 'qt_resource_struct')
        assert isinstance(resources.qt_resource_struct, bytes)

    def test_resource_data_contains_png_signature(self) -> None:
        """Test that resource data contains PNG file signature."""
        # PNG files start with specific signature bytes
        png_signature = b'\x89PNG\r\n\x1a\n'
        assert png_signature in resources.qt_resource_data

    def test_resource_name_structure(self) -> None:
        """Test that resource name structure is not empty."""
        assert len(resources.qt_resource_name) > 0

    def test_resource_struct_structure(self) -> None:
        """Test that resource struct structure is not empty."""
        assert len(resources.qt_resource_struct) > 0
