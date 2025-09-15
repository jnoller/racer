"""
Database utilities for testing.
"""

import os
import tempfile
from typing import Optional
from src.backend.database import DatabaseManager


class TestDatabaseManager:
    """Test database manager that uses a temporary database."""
    
    def __init__(self, database_url: str = None):
        """Initialize with a temporary database."""
        if database_url is None:
            # Create a temporary database file
            self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            self.temp_db.close()
            database_url = f"sqlite:///{self.temp_db.name}"
        
        self.database_url = database_url
        self.db_manager = DatabaseManager(database_url)
        self.db_manager.init_database()
    
    def cleanup(self):
        """Clean up the temporary database."""
        try:
            self.db_manager.cleanup_database()
            if hasattr(self, 'temp_db'):
                os.unlink(self.temp_db.name)
        except Exception:
            pass  # Ignore cleanup errors in tests
    
    def __enter__(self):
        """Context manager entry."""
        return self.db_manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


def get_test_db_manager(database_url: str = None) -> TestDatabaseManager:
    """Get a test database manager."""
    return TestDatabaseManager(database_url)
