import os

os.environ["SEARCH_PROVIDER"] = "mock"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["ZETARIS_API_KEY"] = ""
os.environ["ZETARIS_ORG_ID"] = ""
os.environ["NIGHTSHIFT_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
