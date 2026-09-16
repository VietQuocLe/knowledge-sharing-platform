import os
import sys
import pytest

# Ensure backend root directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import app.models  # noqa: F401 - ensures all model metadata is registered on Base
from app.models.base import Base
from app.core.database import engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Session-level fixture that automatically creates all database tables
    before running tests, ensuring test suites succeed in fresh CI environments.
    """
    Base.metadata.create_all(bind=engine)
    yield
